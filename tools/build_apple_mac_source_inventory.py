#!/usr/bin/env python3
"""Build a source-first inventory of captured Apple Mac Tech Specs pages.

This does not create one product record per URL. It deliberately keeps page
variants visible for a later model-family deduplication review (for example,
connectivity-only or port-count variants must not automatically become separate
products).
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("apple_mac_extraction")
REPORT = ROOT / "extraction_report.json"
OUT = Path("data/apple/mac/source-inventory.json")

FAMILY_PATTERNS = [
    ("MacBook Air", re.compile(r"MacBook Air", re.I)),
    ("MacBook Pro", re.compile(r"MacBook Pro", re.I)),
    ("MacBook", re.compile(r"\bMacBook\b", re.I)),
    ("iMac", re.compile(r"\biMac\b", re.I)),
    ("Mac mini", re.compile(r"Mac mini", re.I)),
    ("Mac Studio", re.compile(r"Mac Studio", re.I)),
    ("Mac Pro", re.compile(r"Mac Pro", re.I)),
]

def family_for(title: str):
    for family, pattern in FAMILY_PATTERNS:
        if pattern.search(title):
            return family
    return None

def is_tech_specs_title(title: str) -> bool:
    return bool(re.search(r"tech specs|technical specifications?", title, re.I))

def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "apple-mac-model"

report = json.loads(REPORT.read_text(encoding="utf-8-sig"))
pages = report.get("technical_spec_pages", [])
inventory = []
excluded = []
seen_urls = set()

for page in pages:
    title = (page.get("title") or "").strip()
    url = page.get("final_url") or page.get("requested_url") or ""
    family = family_for(title)
    if not family or not is_tech_specs_title(title):
        excluded.append({"title": title, "url": url, "reason": "Not a Mac technical-specification page"})
        continue
    if url in seen_urls:
        continue
    seen_urls.add(url)
    year_match = re.search(r"\b(19|20)\d{2}\b", title)
    article_match = re.search(r"/(\d{5,6})(?:$|[?#])", url)
    inventory.append({
        "family": family,
        "model_title": title,
        "model_slug_candidate": slugify(title),
        "year_mentioned_in_title": int(year_match.group(0)) if year_match else None,
        "official_source_url": url,
        "source_file": page.get("saved_file"),
        "http_status": page.get("status"),
        "source_title": title,
        "apple_support_article_id": article_match.group(1) if article_match else None,
        "catalogue_status": "source_captured_pending_model_deduplication_and_content_review"
    })

inventory.sort(key=lambda x: (x["family"], -(x["year_mentioned_in_title"] or 0), x["model_title"]))

# Flag possible sibling variants without merging them. Human review is required.
buckets = defaultdict(list)
for item in inventory:
    year = item["year_mentioned_in_title"] or "unknown"
    screen = re.search(r"\b(11|12|13|14|15|16|17|21\.5|24|27|30)\s*-?inch\b", item["model_title"], re.I)
    buckets[(item["family"], year, screen.group(0).lower() if screen else "unspecified")].append(item)

review_groups = []
for (family, year, screen), items in buckets.items():
    if len(items) > 1:
        review_groups.append({
            "family": family,
            "year": year,
            "screen_size_group": screen,
            "candidate_pages": [x["official_source_url"] for x in items],
            "review_note": "Do not create separate product records until differences are checked. Treat connectivity/port-only differences as variants where appropriate."
        })

counts = defaultdict(int)
for item in inventory:
    counts[item["family"]] += 1

result = {
    "catalogue_stage": "source_inventory_not_final_product_catalogue",
    "source_policy": "Official Apple pages only. Preserve each distinct official URL. Do not equate page count with product count.",
    "summary": {
        "captured_pages_examined": len(pages),
        "mac_technical_spec_pages_in_inventory": len(inventory),
        "excluded_non_mac_or_non_spec_pages": len(excluded),
        "family_counts": dict(sorted(counts.items())),
        "candidate_variant_groups_for_manual_review": len(review_groups)
    },
    "models": inventory,
    "candidate_variant_groups": review_groups,
    "excluded_pages": excluded
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
print(f"Inventory written to {OUT}")
