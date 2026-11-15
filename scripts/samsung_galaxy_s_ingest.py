#!/usr/bin/env python3
"""Discover and archive one standard Samsung Galaxy S model per generation.

Scope is intentionally narrow:
- include Galaxy S, S2 ... S26 standard/base models only;
- exclude Plus, Ultra, FE, Edge, Active, colour and storage SKUs;
- never create one product record per retailer SKU;
- preserve downloaded Samsung Ireland HTML and create archival-first V2 records.

Run from repository root:
    python -m pip install -r requirements.txt
    python scripts/samsung_galaxy_s_ingest.py --discover
    python scripts/samsung_galaxy_s_ingest.py --archive

Discovery writes data/samsung/smartphones/source-inventory.json.
Archive downloads only the selected standard-model pages and writes V2 records.
A page is not marked content_verified merely because it returned HTTP 200.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "samsung" / "smartphones"
SOURCE_DIR = ROOT / "sources" / "samsung" / "galaxy-s"
INVENTORY = DATA_DIR / "source-inventory.json"
BASE = "https://www.samsung.com/ie/"
CATEGORY_URL = urljoin(BASE, "smartphones/")
SITEMAP_URL = urljoin(BASE, "info/sitemap/")
USER_AGENT = "TechSpecsResearchBot/1.0 (+product specification research; contact: techspecs project; low-rate diagnostic)"
DELAY_SECONDS = 2.0
TIMEOUT = 45

# Only the plain, numbered Galaxy S generation is in scope. Plus/Ultra/FE/Edge
# and model-number/colour/storage SKU URLs deliberately do not match.
MODEL_PATH = re.compile(r"^/ie/smartphones/(galaxy-s(?:\d{1,2})?)/?$", re.I)
YEAR_BY_GENERATION = {
    "galaxy-s": 2010, "galaxy-s2": 2011, "galaxy-s3": 2012,
    "galaxy-s4": 2013, "galaxy-s5": 2014, "galaxy-s6": 2015,
    "galaxy-s7": 2016, "galaxy-s8": 2017, "galaxy-s9": 2018,
    "galaxy-s10": 2019, "galaxy-s20": 2020, "galaxy-s21": 2021,
    "galaxy-s22": 2022, "galaxy-s23": 2023, "galaxy-s24": 2024,
    "galaxy-s25": 2025, "galaxy-s26": 2026,
}


def now_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IE,en;q=0.9",
    })
    return session


def canonical_model_url(href: str, page_url: str) -> tuple[str, str] | None:
    absolute = urljoin(page_url, href)
    parsed = urlparse(absolute)
    if parsed.hostname not in {"www.samsung.com", "samsung.com"}:
        return None
    match = MODEL_PATH.match(parsed.path)
    if not match:
        return None
    slug = match.group(1).lower()
    # Do not mistake the unnumbered family landing page for a specific device.
    if slug == "galaxy-s":
        generation = 1
    else:
        digits = slug.removeprefix("galaxy-s")
        if not digits.isdigit():
            return None
        generation = int(digits)
    # Samsung skipped S11-S19 naming. Reject non-canonical numeric slugs.
    if generation not in {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 21, 22, 23, 24, 25, 26}:
        return None
    return slug, f"https://www.samsung.com{parsed.path.rstrip('/')}/"


def discover(session: requests.Session) -> list[dict]:
    candidates: dict[str, dict] = {}
    for source_url in (SITEMAP_URL, CATEGORY_URL):
        response = session.get(source_url, timeout=TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        for anchor in soup.find_all("a", href=True):
            item = canonical_model_url(anchor["href"], source_url)
            if not item:
                continue
            slug, url = item
            candidates[slug] = {
                "slug": slug,
                "model": "Galaxy " + ("S" if slug == "galaxy-s" else "S" + slug.removeprefix("galaxy-s")),
                "year_introduced": YEAR_BY_GENERATION.get(slug),
                "source_url": url,
                "discovery_source": source_url,
                "selection_rule": "standard Galaxy S generation only; Plus/Ultra/FE/Edge and SKU variants excluded",
            }
        time.sleep(DELAY_SECONDS)

    # Current and historical generations may not all remain linked from the
    # live category/sitemap. Keep a deterministic list of canonical historical
    # URL candidates, but mark them undiscovered until an HTTP check succeeds.
    for slug, year in YEAR_BY_GENERATION.items():
        if slug == "galaxy-s":
            continue
        if slug not in candidates:
            candidates[slug] = {
                "slug": slug,
                "model": "Galaxy S" + slug.removeprefix("galaxy-s"),
                "year_introduced": year,
                "source_url": f"https://www.samsung.com/ie/smartphones/{slug}/",
                "discovery_source": None,
                "selection_rule": "canonical historical URL candidate; must pass HTTP and content checks",
                "candidate_status": "not_yet_confirmed",
            }
    return sorted(candidates.values(), key=lambda x: (x.get("year_introduced") or 0, x["slug"]))


def write_inventory(items: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    inventory = {
        "inventory_version": "1.0",
        "brand": "Samsung",
        "category": "smartphone",
        "family": "Galaxy S",
        "market": "Ireland",
        "scope": {
            "included": "One standard/base Galaxy S model per numbered generation",
            "excluded": ["Galaxy S Plus", "Galaxy S Ultra", "Galaxy S FE", "Galaxy S Edge", "Active variants", "colour SKUs", "storage SKUs", "carrier SKUs"],
            "deduplication": "One record per generation; model numbers and storage options are attributes, not separate product records.",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "working_scope": items,
    }
    INVENTORY.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    main = soup.find("main") or soup.body or soup
    lines = []
    for line in main.get_text("\n", strip=True).splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line and (not lines or line != lines[-1]):
            lines.append(line)
    return "\n".join(lines)


def archive_and_record(session: requests.Session, item: dict) -> tuple[str, str]:
    url = item["source_url"]
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    if "text/html" not in response.headers.get("Content-Type", "").lower():
        raise ValueError(f"unexpected content type: {response.headers.get('Content-Type')}")
    text = visible_text(response.text)
    title = BeautifulSoup(response.text, "lxml").title
    title_text = title.get_text(" ", strip=True) if title else item["model"]
    if len(text) < 500:
        raise ValueError("page returned too little readable text; possible shell/consent/interstitial")

    slug = item["slug"]
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    source_path = SOURCE_DIR / f"{slug}.html"
    source_path.write_text(response.text, encoding="utf-8")
    source_rel = source_path.relative_to(ROOT).as_posix()

    year = item.get("year_introduced")
    record = {
        "schema_version": "2.0",
        "product": {
            "brand": "Samsung",
            "category": "smartphone",
            "family": "Galaxy S",
            "model": item["model"],
            "model_slug": slug,
            "model_year": year,
            "year_introduced": year,
            "variant": None,
            "model_numbers": [],
            "finishes": [],
            "storage_options": [],
        },
        "source": {
            "source_type": "manufacturer",
            "source_url": url,
            "source_file": source_rel,
            "source_title": title_text,
            "publisher": "Samsung Electronics",
            "published_at": None,
            "checked_at": now_date(),
            "verification_status": "url_checked",
            "verification_notes": "Official Samsung Ireland page downloaded and archived. Specifications have not yet been field-by-field verified; this is an archival-first record.",
            "notes": ["One standard Galaxy S generation record; no colour, storage, Plus, Ultra, FE or Edge SKU records are created."],
        },
        "extraction": {
            "method": "section_preserving",
            "normalization_status": "archival_first_pass",
            "note": "Visible page text preserved as source evidence. Do not treat unreviewed page text as normalized specifications.",
            "extracted_at": now_date(),
            "reviewed_at": None,
        },
        "sections": [{
            "heading": "Samsung Ireland product page — visible text (archival first pass)",
            "source_text": text,
            "source_url": url,
            "source_file": source_rel,
        }],
        "record_notes": [
            "Generated by scripts/samsung_galaxy_s_ingest.py.",
            "A successful HTTP response does not prove that every specification is present or correct.",
            "The source HTML is retained under sources/samsung/galaxy-s/.",
        ],
    }
    record_path = DATA_DIR / f"{slug}.json"
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return source_rel, record_path.relative_to(ROOT).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--discover", action="store_true", help="discover and list standard Galaxy S generations")
    group.add_argument("--archive", action="store_true", help="download discovered/canonical candidates and create V2 archival-first records")
    args = parser.parse_args()

    session = get_session()
    try:
        if args.discover:
            items = discover(session)
            write_inventory(items)
            confirmed = sum(1 for x in items if x.get("discovery_source"))
            print(f"Inventory written: {INVENTORY.relative_to(ROOT)}")
            print(f"Candidates: {len(items)} | found directly in current pages: {confirmed}")
            print("Only standard Galaxy S generations are listed; no Plus/Ultra/FE/Edge or SKU variants.")
            return 0

        if not INVENTORY.is_file():
            print("ERROR: run --discover first to create the source inventory.", file=sys.stderr)
            return 2
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        items = inventory.get("working_scope", [])
        successes = 0
        failures = []
        for item in items:
            try:
                source_rel, record_rel = archive_and_record(session, item)
                successes += 1
                item["candidate_status"] = "archived_url_checked"
                item["source_file"] = source_rel
                item["record_path"] = record_rel
                print(f"[ARCHIVED] {item['model']}: {record_rel}")
            except Exception as exc:
                item["candidate_status"] = "unavailable_or_unreadable"
                item["error"] = str(exc)
                failures.append((item["model"], str(exc)))
                print(f"[SKIP] {item['model']}: {exc}")
            time.sleep(DELAY_SECONDS)
        write_inventory(items)
        print(f"Archived V2 records: {successes} | unavailable/unreadable: {len(failures)}")
        print("All new records remain archival_first_pass / url_checked until specifications are reviewed.")
        return 0 if successes else 1
    except requests.RequestException as exc:
        print(f"ERROR: Samsung request failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
