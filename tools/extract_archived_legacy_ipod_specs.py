#!/usr/bin/env python3
"""Attach archived legacy iPod technical-specification sections to existing records.

This is an archival/provenance step only: it preserves source sections with their
own URLs and repository paths, but does not infer or populate typed specifications.
"""
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
DATA = ROOT / "data" / "apple" / "ipod"
ARCHIVE_ROOT = "apple_remaining_extraction/technical_specs_html"
IDENTITY_URL = "https://support.apple.com/en-ie/103823"
IDENTITY_FILE = "apple_remaining_extraction/technical_specs_html/ipod-index.html"
TODAY = date.today().isoformat()

# Each mapping is deliberately explicit. Some pages cover a subset of a broader
# historical record; their sections are supporting evidence, not a reason to
# merge storage/year variants or overwrite existing normalized values.
MAPPINGS = [
    {"archive": "ipod-nano-1st-generation-tech-specs.html", "url": "https://support.apple.com/en-ie/112507",
     "models": [{"slug": "ipod-nano", "inventory_model": "iPod nano", "coverage_note": "First-generation iPod nano technical specifications; model/capacity identity remains separately sourced from Apple's identification page."}]},
    {"archive": "ipod-nano-2nd-generation-tech-specs.html", "url": "https://support.apple.com/en-ie/112309",
     "models": [{"slug": "ipod-nano-2nd-generation", "inventory_model": "iPod nano (2nd generation)", "coverage_note": "Second-generation iPod nano technical specifications."}]},
    {"archive": "ipod-nano-3rd-generation-tech-specs.html", "url": "https://support.apple.com/en-ie/112552",
     "models": [{"slug": "ipod-nano-3rd-generation", "inventory_model": "iPod nano (3rd generation)", "coverage_note": "Third-generation iPod nano technical specifications."}]},
    {"archive": "ipod-nano-5th-generation-tech-specs.html", "url": "https://support.apple.com/en-ie/112495",
     "models": [{"slug": "ipod-nano-5th-generation", "inventory_model": "iPod nano (5th generation)", "coverage_note": "Fifth-generation iPod nano technical specifications."}]},
    {"archive": "ipod-shuffle-2nd-generation-tech-specs.html", "url": "https://support.apple.com/en-ie/112455",
     "models": [{"slug": "ipod-shuffle-2nd-generation", "inventory_model": "iPod shuffle (2nd generation)", "coverage_note": "Second-generation iPod shuffle technical specifications."}]},
    {"archive": "ipod-shuffle-3rd-generation-tech-specs.html", "url": "https://support.apple.com/en-ie/112497",
     "models": [{"slug": "ipod-shuffle-3rd-generation", "inventory_model": "iPod shuffle (3rd generation)", "coverage_note": "Third-generation iPod shuffle technical specifications; generation/year variants remain distinct."}]},
    {"archive": "ipod-5th-generation-2005-tech-specs.html", "url": "https://support.apple.com/en-ie/111923",
     "models": [{"slug": "ipod-5th-generation-also-known-as-ipod-with-video-or-fifth-generation-ipod", "inventory_model": "iPod (5th generation) – also known as iPod with video or Fifth Generation iPod", "coverage_note": "The official page covers the 2005 fifth-generation family, including capacity variants; existing typed capacity fields are not changed automatically."}]},
    {"archive": "ipod-5th-generation-late-2006-tech-specs.html", "url": "https://support.apple.com/en-ie/112454",
     "models": [{"slug": "ipod-5th-generation-late-2006-also-known-as-ipod-with-video-or-fifth-generation-ipod", "inventory_model": "iPod (5th generation Late 2006) – also known as iPod with video or Fifth Generation iPod", "coverage_note": "Late-2006 fifth-generation technical specifications; do not merge with the 2005 or U2 variants."}]},
    {"archive": "ipod-click-wheel-20-40gb-tech-specs.html", "url": "https://support.apple.com/en-ie/112541",
     "models": [
       {"slug": "ipod-click-wheel", "inventory_model": "iPod (Click Wheel)", "coverage_note": "Official page covers 20 GB and 40 GB Click Wheel models; retain its explicit capacity scope."},
       {"slug": "ipod-special-edition-u2", "inventory_model": "iPod Special Edition U2", "coverage_note": "Supporting source for the Click Wheel-based U2 variant only; other U2 generations remain distinct."}
     ]},
    {"archive": "ipod-photo-40-60gb-tech-specs.html", "url": "https://support.apple.com/en-ie/112449",
     "models": [{"slug": "ipod-photo-also-known-as-ipod-with-colour-display", "inventory_model": "iPod photo (also known as iPod with colour display)", "coverage_note": "This technical-specification page covers the 40 GB and 60 GB iPod photo models; the record's 30 GB option requires separate evidence."}]},
]

def clean(value: str) -> str:
    value = unescape(value).replace("\xa0", " ")
    value = re.sub(r"[\t ]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()

def extract_sections(soup: BeautifulSoup) -> list[dict[str, str]]:
    out = []
    for group in soup.select("div.gb-group"):
        heading_node = group.find(["h2", "h3", "h4"])
        if not heading_node:
            continue
        clone = BeautifulSoup(str(group), "html.parser")
        for node in clone.find_all(["h1", "h2", "h3", "h4"]):
            node.decompose()
        for node in clone.select("script, style, noscript"):
            node.decompose()
        body = clean(clone.get_text("\n", strip=True))
        heading = clean(heading_node.get_text(" ", strip=True))
        if heading and body:
            out.append({"heading": heading, "source_text": body})
    if not out:
        root = soup.select_one("main") or soup.select_one("article") or soup.body
        current = None
        chunks: list[str] = []
        def flush():
            if current and chunks:
                body = clean("\n".join(chunks))
                if body:
                    out.append({"heading": current, "source_text": body})
        if root:
            for node in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "dt", "dd"]):
                if node.name in {"h1", "h2", "h3", "h4"}:
                    flush()
                    current = clean(node.get_text(" ", strip=True))
                    chunks = []
                elif current:
                    value = clean(node.get_text(" ", strip=True))
                    if value and (not chunks or chunks[-1] != value):
                        chunks.append(value)
            flush()
    seen = set()
    result = []
    for section in out:
        key = (section["heading"], section["source_text"])
        if key not in seen:
            seen.add(key)
            result.append(section)
    return result

def main() -> int:
    inventory_path = DATA / "source-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    scope = inventory.get("working_scope", [])
    if not isinstance(scope, list):
        raise RuntimeError("iPod source inventory has no working_scope array")
    inventory_by_slug = {str(item.get("slug") or item.get("model_slug") or ""): item for item in scope if isinstance(item, dict)}
    records_updated = sections_added = 0

    for mapping in MAPPINGS:
        archive_rel = f"{ARCHIVE_ROOT}/{mapping['archive']}"
        archive_path = ROOT / archive_rel
        if not archive_path.is_file():
            raise FileNotFoundError(f"Required official iPod archive is missing: {archive_rel}")
        html = archive_path.read_text(encoding="utf-8-sig", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        title_node = soup.find("title")
        title = clean(title_node.get_text(" ", strip=True)) if title_node else mapping["archive"]
        canonical_node = soup.select_one('link[rel="canonical"]')
        canonical_url = clean(canonical_node.get("href", "")) if canonical_node else mapping["url"]
        parsed = urlparse(canonical_url)
        if parsed.scheme != "https" or parsed.hostname != "support.apple.com":
            raise RuntimeError(f"Unexpected canonical Apple source URL: {canonical_url}")
        if not re.search(r"technical specifications|tech specs", title, re.I):
            raise RuntimeError(f"Expected a technical-specification page, got title {title!r}")
        page_sections = extract_sections(soup)
        if not page_sections:
            raise RuntimeError(f"No source sections extracted from {archive_rel}")
        print(f"SOURCE {archive_rel}: {title}; sections={len(page_sections)}; canonical={canonical_url}")

        for model in mapping["models"]:
            slug = model["slug"]
            record_path = DATA / f"{slug}.json"
            if not record_path.is_file():
                raise FileNotFoundError(f"Mapped iPod record is missing: {record_path.relative_to(ROOT)}")
            record = json.loads(record_path.read_text(encoding="utf-8"))
            source = record.setdefault("source", {})
            existing_sections = record.get("sections", [])
            if not isinstance(existing_sections, list):
                raise RuntimeError(f"{slug}: sections is not an array")
            # Give existing identification-page sections explicit provenance before
            # adding sections from the model-specific technical-specification page.
            for section in existing_sections:
                if isinstance(section, dict):
                    section.setdefault("source_url", source.get("source_url") or IDENTITY_URL)
                    section.setdefault("source_file", source.get("source_file") or IDENTITY_FILE)
            existing_keys = {
                (s.get("heading"), s.get("source_text"), s.get("source_url"), s.get("source_file"))
                for s in existing_sections if isinstance(s, dict)
            }
            added = 0
            for section in page_sections:
                enriched = {
                    "heading": section["heading"],
                    "source_text": section["source_text"],
                    "source_url": canonical_url,
                    "source_file": archive_rel,
                }
                key = (enriched["heading"], enriched["source_text"], enriched["source_url"], enriched["source_file"])
                if key not in existing_keys:
                    existing_sections.append(enriched)
                    existing_keys.add(key)
                    added += 1
            record["sections"] = existing_sections
            note = f"Model-specific Apple technical-specification source preserved section-by-section from {canonical_url} ({archive_rel}); {model['coverage_note']} Typed normalized values were not inferred by this archival pass."
            source_notes = source.setdefault("notes", [])
            if note not in source_notes:
                source_notes.append(note)
            extraction = record.setdefault("extraction", {})
            extraction_note = extraction.get("note", "")
            addendum = " Model-specific technical-specification sections are preserved with section-level source_url/source_file; this archival pass does not populate or upgrade typed normalized fields."
            if addendum.strip() not in extraction_note:
                extraction["note"] = (extraction_note + addendum).strip()
            record_notes = record.setdefault("record_notes", [])
            if note not in record_notes:
                record_notes.append(note)
            record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            records_updated += 1
            sections_added += added
            print(f"UPDATED {record_path.relative_to(ROOT)}: added {added} source sections")

            inv_item = inventory_by_slug.get(slug)
            if not inv_item:
                raise RuntimeError(f"{slug}: no matching working_scope entry in source inventory")
            inv_item["technical_spec_source_url"] = canonical_url
            inv_item["technical_spec_source_file"] = archive_rel
            inv_item["technical_spec_source_title"] = title
            inv_item["technical_spec_section_count"] = len(page_sections)
            inv_item["technical_spec_status"] = "archived_section_mapped_pending_field_verification"
            inv_item["technical_spec_coverage_note"] = model["coverage_note"]
            inv_item["technical_spec_checked_at"] = TODAY

    inventory["record_audit"] = inventory.get("record_audit", {})
    audit = inventory["record_audit"]
    audit["checked_at"] = TODAY
    audit.setdefault("completed", [])
    completion = f"Archived and mapped ten official Apple technical-specification pages to {records_updated} existing iPod records with section-level URL and archive-path provenance; no typed specification values were inferred."
    if completion not in audit["completed"]:
        audit["completed"].append(completion)
    audit.setdefault("remaining", [])
    inventory.setdefault("notes", []).append(
        f"{TODAY} archival mapping pass: ten additional official Apple iPod technical-specification archives are now attached to existing records with section-level provenance. Existing identification-page facts and distinct capacity/year variants were retained; typed specification normalization remains pending field-by-field review."
    )
    # Keep the archival status explicit in the inventory without implying all
    # 37 model/date/capacity variants are fully verified.
    inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"RESULT: updated {records_updated} records; added {sections_added} section entries.")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
