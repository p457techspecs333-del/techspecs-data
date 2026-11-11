#!/usr/bin/env python3
"""Extract archived official technical-specification sections for legacy Apple Watch records.

This script never fetches the network and never overwrites normalized specification
fields. It reads the original HTML and metadata sidecars produced by
scripts/archive_official_sources.py, checks model identity, and replaces only the
archival-first-pass sections/provenance for the ten older Watch records.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "apple_watch_extraction" / "technical_specs_html"
DATA_DIR = ROOT / "data" / "apple" / "watch"
INVENTORY_PATH = DATA_DIR / "source-inventory.json"
IDENTITY_FILE = "apple-watch-model-identification.html"
IDENTITY_URL = "https://support.apple.com/en-ie/108056"
TODAY = datetime.now(timezone.utc).date().isoformat()

TARGETS = [
    ("apple-watch-first-generation", "Apple Watch (1st generation)", "apple-watch-first-generation-tech-specs.html"),
    ("apple-watch-series-1", "Apple Watch Series 1", "apple-watch-series-1-tech-specs.html"),
    ("apple-watch-series-2", "Apple Watch Series 2", "apple-watch-series-2-tech-specs.html"),
    ("apple-watch-series-3", "Apple Watch Series 3", "apple-watch-series-3-tech-specs.html"),
    ("apple-watch-series-4", "Apple Watch Series 4", "apple-watch-series-4-tech-specs.html"),
    ("apple-watch-series-5", "Apple Watch Series 5", "apple-watch-series-5-tech-specs.html"),
    ("apple-watch-series-6", "Apple Watch Series 6", "apple-watch-series-6-tech-specs.html"),
    ("apple-watch-series-7", "Apple Watch Series 7", "apple-watch-series-7-tech-specs.html"),
    ("apple-watch-se-1", "Apple Watch SE (1st generation)", "apple-watch-se-1-tech-specs.html"),
    ("apple-watch-ultra", "Apple Watch Ultra", "apple-watch-ultra-tech-specs.html"),
]


def clean(value: str) -> str:
    value = (value or "").replace("\xa0", " ")
    value = re.sub(r"[\t ]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def parse_sections(soup: BeautifulSoup) -> list[dict]:
    out = []
    # Apple Support's current and legacy technical-specification page layout.
    for group in soup.select("div.gb-group"):
        heading_node = group.find(["h2", "h3", "h4"])
        if not heading_node:
            continue
        heading = clean(heading_node.get_text(" ", strip=True))
        body = BeautifulSoup(str(group), "html.parser")
        for node in body.find_all(["h2", "h3", "h4"]):
            node.decompose()
        for node in body.select("script,style,noscript"):
            node.decompose()
        source_text = clean(body.get_text("\n", strip=True))
        if heading and source_text:
            out.append({"heading": heading, "source_text": source_text})
    # Fallback for older layouts where content is not wrapped in gb-group.
    if not out:
        root = soup.select_one("main") or soup.select_one("article") or soup.body
        if root:
            current = None
            chunks = []
            for node in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "dt", "dd"]):
                if node.name in {"h1", "h2", "h3", "h4"}:
                    if current and chunks:
                        text = clean("\n".join(chunks))
                        if text:
                            out.append({"heading": current, "source_text": text})
                    current = clean(node.get_text(" ", strip=True))
                    chunks = []
                elif current:
                    value = clean(node.get_text(" ", strip=True))
                    if value and (not chunks or chunks[-1] != value):
                        chunks.append(value)
            if current and chunks:
                text = clean("\n".join(chunks))
                if text:
                    out.append({"heading": current, "source_text": text})
    unique = []
    seen = set()
    for section in out:
        key = (section["heading"], section["source_text"])
        if key not in seen:
            seen.add(key)
            unique.append(section)
    return unique


def metadata_for(path: Path) -> dict:
    meta_path = path.with_suffix(path.suffix + ".metadata.json")
    if not path.is_file() or not meta_path.is_file():
        raise RuntimeError(f"Missing archived HTML or metadata sidecar: {path.relative_to(ROOT)}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def verify_identity(soup: BeautifulSoup, expected: str, title: str) -> None:
    h1 = soup.find("h1")
    visible = clean(h1.get_text(" ", strip=True)) if h1 else title
    normalized = re.sub(r"[^a-z0-9]+", " ", visible.casefold()).strip()
    expected_normalized = re.sub(r"[^a-z0-9]+", " ", expected.casefold()).strip()
    if expected_normalized not in normalized and normalized not in expected_normalized:
        # Apple Watch first-generation pages sometimes shorten the heading to
        # "Apple Watch"; use the verified archive title as a secondary check.
        title_normalized = re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()
        if expected_normalized not in title_normalized and not (
            expected == "Apple Watch (1st generation)" and "apple watch" in title_normalized and "1st generation" in title_normalized
        ):
            raise RuntimeError(f"Model identity mismatch: expected {expected!r}, h1={visible!r}, title={title!r}")


def main() -> int:
    identity_path = HTML_DIR / IDENTITY_FILE
    identity_meta = metadata_for(identity_path)
    identity_soup = BeautifulSoup(identity_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    identity_title = str(identity_meta.get("page_title") or "")
    if "identify your apple watch" not in identity_title.casefold():
        raise RuntimeError(f"Unexpected Apple Watch identity source title: {identity_title!r}")

    results = []
    for slug, expected, filename in TARGETS:
        html_path = HTML_DIR / filename
        meta = metadata_for(html_path)
        soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
        title = str(meta.get("page_title") or "")
        verify_identity(soup, expected, title)
        extracted = parse_sections(soup)
        if not extracted:
            raise RuntimeError(f"No specification sections extracted from {html_path.relative_to(ROOT)}")
        spec_url = str(meta.get("canonical_url") or meta.get("final_url") or "")
        if not spec_url.startswith("https://support.apple.com/"):
            raise RuntimeError(f"Unexpected non-Apple Support canonical URL for {expected}: {spec_url!r}")

        record_path = DATA_DIR / f"{slug}.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        old_sections = record.get("sections") if isinstance(record.get("sections"), list) else []
        identity_section = next(
            (dict(section) for section in old_sections if isinstance(section, dict) and section.get("heading") == "Model identification"),
            {"heading": "Model identification", "source_text": f"{expected}. Year introduced: {record.get('product', {}).get('year_introduced')}."},
        )
        identity_section["source_url"] = str(identity_meta.get("canonical_url") or identity_meta.get("final_url") or IDENTITY_URL)
        identity_section["source_file"] = identity_path.relative_to(ROOT).as_posix()

        sourced_sections = []
        for section in extracted:
            section["source_url"] = spec_url
            section["source_file"] = html_path.relative_to(ROOT).as_posix()
            sourced_sections.append(section)

        previous_source = record.get("source") if isinstance(record.get("source"), dict) else {}
        source_changed = previous_source.get("source_file") != html_path.relative_to(ROOT).as_posix() or previous_source.get("source_url") != spec_url
        record["source"] = {
            **previous_source,
            "source_type": "manufacturer",
            "source_url": spec_url,
            "source_file": html_path.relative_to(ROOT).as_posix(),
            "source_title": title,
            "publisher": "Apple Support",
            "checked_at": TODAY if source_changed or not previous_source.get("checked_at") else previous_source.get("checked_at"),
            "verification_status": "content_verified",
            "verification_notes": (
                f"Official Apple technical-specification HTML archived with a SHA-256 sidecar; "
                f"page identity matched {expected!r}; {len(sourced_sections)} specification sections extracted. "
                f"Model identity and year-introduced evidence is retained separately from Apple's "
                f"identification page at {IDENTITY_URL}."
            ),
            "notes": [
                "Technical specification sections are transcribed from the archived model-specific Apple Support page; every section retains its own source URL and archive path.",
                f"Model identity/year evidence is separately sourced from {IDENTITY_URL}, archived at {identity_path.relative_to(ROOT).as_posix()}.",
                "This is an archival-first extraction; normalized values have not been inferred from the section text."
            ],
        }
        record["sections"] = [identity_section, *sourced_sections]
        extraction = record.get("extraction") if isinstance(record.get("extraction"), dict) else {}
        record["extraction"] = {
            **extraction,
            "method": "section_preserving",
            "normalization_status": "archival_first_pass",
            "note": "Official Apple technical-specification source text is retained by section. Existing product identity fields are preserved; no normalized specifications have been inferred.",
            "extracted_at": TODAY if source_changed or extraction.get("method") != "section_preserving" else extraction.get("extracted_at", TODAY),
            "reviewed_at": extraction.get("reviewed_at"),
        }
        notes = record.get("record_notes") if isinstance(record.get("record_notes"), list) else []
        audit_note = "Technical specification sections now come from the archived model-specific Apple Support page; model/year identity is separately sourced from Apple's identification page."
        if audit_note not in notes:
            notes.append(audit_note)
        record["record_notes"] = notes
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        results.append({
            "record_path": record_path.relative_to(ROOT).as_posix(),
            "model": expected,
            "technical_source_url": spec_url,
            "technical_source_file": html_path.relative_to(ROOT).as_posix(),
            "identity_source_file": identity_path.relative_to(ROOT).as_posix(),
            "sections_extracted": len(sourced_sections),
            "verification_status": "content_verified",
        })

    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    scope = inventory.get("working_scope") if isinstance(inventory.get("working_scope"), list) else []
    for result in results:
        item = {
            "model": result["model"],
            "record_path": result["record_path"],
            "source_url": result["technical_source_url"],
            "source_verification_status": "content_verified",
            "extraction_status": "extracted",
            "section_count": result["sections_extracted"] + 1,
            "source_file": result["technical_source_file"],
            "identity_source_file": result["identity_source_file"],
        }
        slug = Path(result["record_path"]).stem
        index = next((i for i, existing in enumerate(scope) if isinstance(existing, dict) and (existing.get("slug") == slug or Path(str(existing.get("record_path", ""))).stem == slug)), None)
        if index is None:
            item["slug"] = slug
            scope.append(item)
        else:
            scope[index] = {**scope[index], **item, "slug": slug}
    inventory["working_scope"] = scope
    inventory_notes = inventory.get("notes") if isinstance(inventory.get("notes"), list) else []
    note = f"Legacy Watch technical-specification archive/extraction completed {TODAY}: ten records now retain model-specific source sections plus separate model-identification provenance."
    if note not in inventory_notes:
        inventory_notes.append(note)
    inventory["notes"] = inventory_notes
    INVENTORY_PATH.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "completed_date_utc": TODAY,
        "purpose": "Section-preserving extraction from archived official Apple Watch technical-specification pages.",
        "identity_source": {"url": identity_meta.get("canonical_url") or identity_meta.get("final_url") or IDENTITY_URL, "file": identity_path.relative_to(ROOT).as_posix()},
        "summary": {"records_updated": len(results), "records_with_identity_source": len(results), "records_with_specification_sections": sum(r["sections_extracted"] > 0 for r in results), "specification_sections_extracted": sum(r["sections_extracted"] for r in results)},
        "results": results,
        "limitations": ["This extraction preserves original source sections and does not independently validate every normalized product field.", "No normalized specifications are inferred or written by this script."]
    }
    report_path = ROOT / "apple_watch_extraction" / "legacy_specs_extraction_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    for item in results:
        print(f"PASS {item['model']}: {item['sections_extracted']} source sections")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
