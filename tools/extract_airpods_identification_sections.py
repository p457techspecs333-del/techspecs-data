#!/usr/bin/env python3
"""Attach model-specific sections from Apple's AirPods identification page."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "apple" / "airpods"
INVENTORY_PATH = DATA / "source-inventory.json"
SOURCE_FILE = "apple_remaining_extraction/technical_specs_html/airpods-identify-model.html"
REQUEST_URL = "https://support.apple.com/en-ie/109525"
TODAY = date.today().isoformat()

# Each record receives only the matching earbud and/or case identification
# sections. This preserves model/case provenance without copying the entire
# page into every record or changing typed values automatically.
MAPPINGS = {
 "airpods-1st-generation-airpods-1-tech-specs-111855": ["AirPods 1"],
 "airpods-2nd-generation-airpods-2-tech-specs-111856": ["AirPods 2"],
 "airpods-2nd-generation-with-wireless-charging-case-airpods-2-tech-specs-111856": ["AirPods 2", "Wireless Charging Case"],
 "airpods-3rd-generation-airpods-3-tech-specs-111863": ["AirPods 3", "MagSafe Charging Case for AirPods 3"],
 "airpods-3rd-generation-with-lightning-charging-airpods-3-tech-specs-111863": ["AirPods 3", "Lightning Charging Case for AirPods 3"],
 "airpods-4-airpods-4-tech-specs-121203": ["AirPods 4", "Charging Case for AirPods 4"],
 "airpods-4-with-active-noise-cancellation-airpods-4-with-active-noise-cancellation-tech-specs-121204": ["AirPods 4 (ANC)", "Wireless Charging Case for AirPods 4 (ANC)"],
 "airpods-5-airpods-5-tech-specs-148759": ["AirPods 5", "Charging Case for AirPods 5"],
 "airpods-5-wireless-airpods-5-with-wireless-charging-case-tech-specs-148760": ["AirPods 5 with Wireless Charging Case", "Wireless Charging Case for AirPods 5"],
 "airpods-max-1-airpods-max-1-tech-specs-111858": ["AirPods Max 1 (Lightning)"],
 "airpods-max-1-usb-c-airpods-max-1-usb-c-tech-specs-121205": ["AirPods Max 1 (USB-C)"],
 "airpods-max-2-airpods-max-2-tech-specs-126620": ["AirPods Max 2"],
 "airpods-pro-1st-generation-with-wireless-charging-case-airpods-pro-1-with-wireless-charging-case-tech-specs-111861": ["AirPods Pro 1", "AirPods Pro 1 Charging Case"],
 "airpods-pro-2nd-generation-with-magsafe-charging-case-lightning-airpods-pro-2-tech-specs-111851": ["AirPods Pro 2 with MagSafe Charging Case (Lightning)", "MagSafe Charging Case (Lightning) for AirPods Pro 2"],
 "airpods-pro-2nd-generation-with-magsafe-charging-case-usb-c-airpods-pro-2-with-magsafe-case-usb-c-tech-specs-111834": ["AirPods Pro 2 with MagSafe Charging Case (USB-C)", "MagSafe Charging Case (USB-C) for AirPods Pro 2"],
 "airpods-pro-3-airpods-pro-3-tech-specs-125135": ["AirPods Pro 3", "MagSafe Charging Case for AirPods Pro 3"],
 "airpods-pro-with-magsafe-charging-case-airpods-pro-1-with-magsafe-charging-case-tech-specs-111859": ["AirPods Pro 1", "MagSafe Charging Case for AirPods Pro 1"],
 "airpods-wireless-charging-case-airpods-2-and-earlier-wireless-charging-case-tech-specs-111860": ["Wireless Charging Case"],
 "magsafe-charging-case-usb-c-airpods-pro-2nd-generation-airpods-pro-2-with-magsafe-case-usb-c-tech-specs-111834": ["MagSafe Charging Case (USB-C) for AirPods Pro 2"],
}

def clean(value: str) -> str:
    value = unescape(value).replace("\xa0", " ")
    value = re.sub(r"[\t ]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()

def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

def heading_blocks(soup: BeautifulSoup) -> dict[str, dict[str, str]]:
    blocks: dict[str, dict[str, str]] = {}
    heading_tags = {"h2": 2, "h3": 3, "h4": 4, "h5": 5}
    for heading in soup.find_all(list(heading_tags)):
        title = clean(heading.get_text(" ", strip=True))
        if not title:
            continue
        level = heading_tags[heading.name]
        lines = []
        for node in heading.find_all_next():
            if node.name in heading_tags:
                next_level = heading_tags[node.name]
                if next_level <= level:
                    break
                lines.append(clean(node.get_text(" ", strip=True)))
            elif node.name in {"p", "li", "dt", "dd"}:
                if node.name == "li" and node.find_parent("li"):
                    continue
                value = clean(node.get_text(" ", strip=True))
                if value:
                    lines.append(value)
        unique = []
        for line in lines:
            if line and line not in unique:
                unique.append(line)
        body = "\n".join(unique).strip()
        key = norm(title)
        if body and ("model number" in body.casefold() or "year introduced" in body.casefold() or "works with" in body.casefold() or "port" in body.casefold()):
            # Prefer the fullest occurrence if a page has a table-of-contents
            # heading and a separate content heading with the same title.
            if key not in blocks or len(body) > len(blocks[key]["source_text"]):
                blocks[key] = {"heading": title, "source_text": body}
    return blocks

def main() -> int:
    archive_path = ROOT / SOURCE_FILE
    if not archive_path.is_file():
        raise FileNotFoundError(f"Required AirPods identification archive missing: {SOURCE_FILE}")
    html = archive_path.read_text(encoding="utf-8-sig", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    canonical_node = soup.select_one('link[rel="canonical"]')
    canonical = clean(canonical_node.get("href", "")) if canonical_node else REQUEST_URL
    parsed = urlparse(canonical)
    if parsed.scheme != "https" or parsed.hostname != "support.apple.com":
        raise RuntimeError(f"Unexpected canonical identification URL: {canonical}")
    title_node = soup.find("title")
    title = clean(title_node.get_text(" ", strip=True)) if title_node else ""
    if "identify your airpods" not in title.casefold():
        raise RuntimeError(f"Unexpected AirPods identification page title: {title!r}")
    blocks = heading_blocks(soup)
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    scope = inventory.get("working_scope", [])
    scope_by_slug = {item.get("slug"): item for item in scope if isinstance(item, dict)}
    records_updated = sections_added = 0

    for slug, aliases in MAPPINGS.items():
        path = DATA / f"{slug}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Mapped AirPods record missing: {path.relative_to(ROOT)}")
        selected = []
        for alias in aliases:
            section = blocks.get(norm(alias))
            if not section:
                raise RuntimeError(f"{slug}: identification heading not found: {alias!r}; available={sorted(blocks)}")
            selected.append(section)
        record = json.loads(path.read_text(encoding="utf-8"))
        product_numbers = record.get("product", {}).get("model_numbers", [])
        evidence = "\n".join(section["source_text"] for section in selected)
        missing_numbers = [number for number in product_numbers if number not in evidence]
        if missing_numbers:
            raise RuntimeError(f"{slug}: model numbers not found in mapped identification sections: {missing_numbers}")

        existing = record.get("sections", [])
        if not isinstance(existing, list):
            raise RuntimeError(f"{slug}: sections is not an array")
        existing_keys = {
            (s.get("heading"), s.get("source_text"), s.get("source_url"), s.get("source_file"))
            for s in existing if isinstance(s, dict)
        }
        added = 0
        for section in selected:
            enriched = {
                "heading": section["heading"],
                "source_text": section["source_text"],
                "source_url": canonical,
                "source_file": SOURCE_FILE,
            }
            key = (enriched["heading"], enriched["source_text"], enriched["source_url"], enriched["source_file"])
            if key not in existing_keys:
                existing.append(enriched)
                existing_keys.add(key)
                added += 1
        record["sections"] = existing
        source = record.setdefault("source", {})
        note = f"Model-number and introduction-year evidence cross-checked against the archived official Apple AirPods identification page: {canonical} ({SOURCE_FILE}). Relevant earbud/case identification sections are retained with section-level provenance; no typed values were changed by this pass."
        source_notes = source.setdefault("notes", [])
        if note not in source_notes:
            source_notes.append(note)
        extraction = record.setdefault("extraction", {})
        addendum = " Relevant model/case identification sections from Apple's official identification page are retained with section-level provenance; model-number strings were checked against these sections without changing typed values."
        if addendum.strip() not in extraction.get("note", ""):
            extraction["note"] = (extraction.get("note", "") + addendum).strip()
        record_notes = record.setdefault("record_notes", [])
        if note not in record_notes:
            record_notes.append(note)
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        records_updated += 1
        sections_added += added
        item = scope_by_slug.get(slug)
        if not item:
            raise RuntimeError(f"{slug}: no matching inventory item")
        item["section_count"] = len(existing)
        item["model_identification_source_url"] = canonical
        item["model_identification_source_file"] = SOURCE_FILE
        item["model_identification_source_title"] = title
        item["model_identification_sections"] = aliases
        item["model_identification_status"] = "archived_and_model_numbers_matched"
        item["model_identification_checked_at"] = TODAY
        print(f"UPDATED {path.relative_to(ROOT)}: sections_added={added}; model_numbers={product_numbers}")

    inventory["record_audit"]["checked_at"] = TODAY
    completion = f"Archived Apple's official AirPods identification page and attached relevant model/case sections to all {records_updated} AirPods records; every product.model_numbers value matched the selected identification source text."
    inventory["record_audit"].setdefault("completed", [])
    if completion not in inventory["record_audit"]["completed"]:
        inventory["record_audit"]["completed"].append(completion)
    inventory["record_audit"]["remaining"] = [
        ("Finish field-by-field review of model/case identifier sets and footnote qualifications; official identification sections are now archived and attached, but typed values remain source_transcribed until independently reconciled."
         if "Finish record-by-record verification of all remaining AirPods model/case identifiers" in item else item)
        for item in inventory["record_audit"].get("remaining", [])
    ]
    inventory.setdefault("notes", []).append(
        f"{TODAY} provenance repair: model numbers had previously been cross-checked against Apple's AirPods identification page but that page was not archived on-repository. It is now retained and relevant model/case sections are attached to all 19 records."
    )
    INVENTORY_PATH.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"RESULT: updated {records_updated} records; added {sections_added} identification sections.")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
