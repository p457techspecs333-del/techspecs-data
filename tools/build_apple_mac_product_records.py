#!/usr/bin/env python3
"""Create schema-v2 archival-first Apple Mac product records from captured Apple HTML.

Each record preserves Apple's visible section headings and text. This script does
not normalize specifications or decide whether sibling pages are distinct retail
SKUs. Those decisions remain for a later model/variant review.
"""
from __future__ import annotations

import json
import re
import html as html_lib
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

ROOT = Path("apple_mac_extraction")
REPORT_PATH = ROOT / "extraction_report.json"
OUT_ROOT = Path("data/apple/mac")
CHECKED_AT = "2026-11-08"

FAMILIES = [
    ("MacBook Air", re.compile(r"MacBook Air", re.I), "macbook-air"),
    ("MacBook Pro", re.compile(r"MacBook Pro", re.I), "macbook-pro"),
    ("MacBook", re.compile(r"\bMacBook\b", re.I), "macbook"),
    ("iMac", re.compile(r"\biMac\b", re.I), "imac"),
    ("Mac mini", re.compile(r"Mac mini", re.I), "mac-mini"),
    ("Mac Studio", re.compile(r"Mac Studio", re.I), "mac-studio"),
    ("Mac Pro", re.compile(r"Mac Pro", re.I), "mac-pro"),
]

def clean_text(value: str) -> str:
    value = html_lib.unescape(value).replace("\xa0", " ")
    value = re.sub(r"[\t ]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()

def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "apple-mac-model"

def identify_family(title: str):
    for family, pattern, folder in FAMILIES:
        if pattern.search(title):
            return family, folder
    return None, None

def section_records(soup: BeautifulSoup):
    sections = []
    # Apple Support's current Tech Specs pages use one .gb-group per section.
    for group in soup.select("div.gb-group"):
        heading_node = group.find(["h2", "h3", "h4"], recursive=False)
        if heading_node is None:
            heading_node = group.find(["h2", "h3", "h4"])
        if heading_node is None:
            continue
        heading = clean_text(heading_node.get_text(" ", strip=True))
        body = BeautifulSoup(str(group), "html.parser")
        for node in body.find_all(["h2", "h3", "h4"]):
            node.decompose()
        for node in body.select("script, style, noscript"):
            node.decompose()
        source_text = clean_text(body.get_text("\n", strip=True))
        if heading and source_text:
            sections.append({"heading": heading, "source_text": source_text})
    # Fallback for older page layouts, retaining heading-to-content blocks.
    if not sections:
        root = soup.select_one("main") or soup.select_one("article") or soup.body
        if root:
            current = None
            chunks = []
            for node in root.find_all(["h2", "h3", "h4", "p", "li"]):
                if node.name in {"h2", "h3", "h4"}:
                    if current and chunks:
                        sections.append({"heading": current, "source_text": clean_text("\n".join(chunks))})
                    current, chunks = clean_text(node.get_text(" ", strip=True)), []
                elif current:
                    text = clean_text(node.get_text(" ", strip=True))
                    if text:
                        chunks.append(text)
            if current and chunks:
                sections.append({"heading": current, "source_text": clean_text("\n".join(chunks))})
    # Remove exact duplicate heading/text pairs without altering source order.
    seen = set()
    unique = []
    for section in sections:
        key = (section["heading"], section["source_text"])
        if key not in seen:
            seen.add(key)
            unique.append(section)
    return unique

def main():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8-sig"))
    generated, skipped = [], []
    for page in report.get("technical_spec_pages", []):
        title = (page.get("title") or "").strip()
        url = page.get("final_url") or page.get("requested_url") or ""
        relative = page.get("saved_file")
        if not title or not url or not relative:
            skipped.append({"title": title, "reason": "Missing title, URL, or saved source file"})
            continue
        family, folder = identify_family(title)
        if not family or not re.search(r"Tech Specs|Technical Specifications", title, re.I):
            skipped.append({"title": title, "reason": "Not a family-specific Mac Tech Specs page"})
            continue
        source_path = Path(relative)
        if not source_path.exists():
            skipped.append({"title": title, "reason": f"Captured HTML not found: {relative}"})
            continue
        raw = source_path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        h1 = soup.find("h1")
        display_title = clean_text(h1.get_text(" ", strip=True)) if h1 else title
        model = re.sub(r"\s*-\s*Tech Specs.*$", "", display_title, flags=re.I).strip()
        year_match = re.search(r"\b(19|20)\d{2}\b", model)
        year = int(year_match.group(0)) if year_match else None
        # Canonical source URL is taken from the page itself where possible.
        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href", "").startswith("https://support.apple.com/"):
            url = canonical["href"]
        sections = section_records(soup)
        if not sections:
            skipped.append({"title": title, "reason": "No specification sections could be extracted"})
            continue
        slug = slugify(model)
        out_dir = OUT_ROOT / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{slug}.json"
        if out_path.exists():
            skipped.append({"title": title, "reason": f"Refusing to overwrite existing record: {out_path.as_posix()}"})
            continue
        model_year = year if year is not None and year >= 2007 else None
        notes = [
            "Archival-first-pass record generated from the captured official Apple Support Tech Specs HTML.",
            "Original Apple section headings and visible source text are retained. No normalized specifications have been inferred.",
            "A separate Apple specification page is not automatically treated as a separate retail SKU; family and configuration deduplication remains a review step."
        ]
        if year is not None and year < 2007:
            notes.append(f"Apple page title indicates {year}; schema v2 model_year minimum is 2007, so model_year is null pending schema policy review.")
        record = {
            "schema_version": "2.0",
            "product": {
                "brand": "Apple",
                "category": "computer",
                "family": family,
                "model": model,
                "model_slug": slug,
                "model_year": model_year,
                "year_introduced": model_year
            },
            "source": {
                "source_type": "manufacturer",
                "source_url": url,
                "source_file": relative,
                "source_title": display_title,
                "publisher": "Apple Support (Ireland)",
                "published_at": None,
                "checked_at": CHECKED_AT,
                "verification_status": "url_checked",
                "verification_notes": "Official Apple Support page returned successfully and its HTML was archived. Original visible specification sections were extracted; individual field values have not yet been independently normalized or verified."
            },
            "extraction": {
                "method": "section_preserving",
                "normalization_status": "archival_first_pass",
                "note": "Apple's original section headings and visible source text are retained in source order. Connectivity, port, memory, storage and other configurations remain within the same source record where Apple presents them together.",
                "extracted_at": CHECKED_AT,
                "reviewed_at": None
            },
            "sections": sections,
            "record_notes": notes
        }
        out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        generated.append({
            "family": family, "model": model, "path": out_path.as_posix(),
            "source_url": url, "section_count": len(sections), "year": year
        })
    summary = {
        "schema_version": "2.0",
        "stage": "archival_first_pass_not_final_deduplicated_catalogue",
        "generated_record_count": len(generated),
        "skipped_count": len(skipped),
        "family_counts": {family: sum(1 for x in generated if x["family"] == family) for family, _, _ in FAMILIES},
        "records": generated,
        "skipped": skipped
    }
    (OUT_ROOT / "generation-report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k not in {"records","skipped"}}, indent=2))
    print(f"Generation report: {OUT_ROOT / 'generation-report.json'}")

if __name__ == "__main__":
    main()
