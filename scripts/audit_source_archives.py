#!/usr/bin/env python3
"""Diagnose product-record provenance against archived HTML at record and section level."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
SKIP = {"catalogue.json", "api-manifest.json", "generation-report.json", "source-inventory.json"}

class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title_parts = []
        self.canonical = None
    def handle_starttag(self, tag, attrs):
        attrs = {k.lower(): v for k, v in attrs}
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "link" and (attrs.get("rel") or "").lower() == "canonical":
            self.canonical = attrs.get("href")
    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False
    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)

def norm(value):
    value = re.sub(r"\s+", " ", value or "").strip().casefold()
    value = value.replace("\u00ad", "").replace("\u2011", "-")
    return re.sub(r"\s*[-–|]\s*apple support(?:\s*\([^)]*\))?$", "", value)

def same_article(a, b):
    if not a or not b:
        return True
    pa, pb = urlparse(a), urlparse(b)
    if pa.hostname != pb.hostname:
        return False
    if pa.hostname and pa.hostname.lower().endswith("apple.com"):
        aa = [p for p in pa.path.split("/") if p]
        bb = [p for p in pb.path.split("/") if p]
        return bool(aa and bb and aa[-1] == bb[-1])
    return pa.path.rstrip("/") == pb.path.rstrip("/")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="fail on missing archives, title mismatches or canonical URL mismatches")
    args = ap.parse_args()
    count = records_with_html = refs = 0
    metadata = {}
    titles = []
    canonicals = []
    missing = []
    hashes = defaultdict(list)

    for path in sorted(DATA_ROOT.rglob("*.json")):
        if path.name in SKIP or "schemas" in path.relative_to(DATA_ROOT).parts:
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(record, dict):
            continue
        count += 1
        record_rel = path.relative_to(ROOT).as_posix()
        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        refs_for_record = []
        if source.get("source_file") and str(source.get("source_file")).lower().endswith((".html", ".htm")):
            refs_for_record.append(("record.source", source.get("source_file"), source.get("source_url"), source.get("source_title")))
        sections = record.get("sections")
        if isinstance(sections, list):
            for index, section in enumerate(sections):
                if isinstance(section, dict) and section.get("source_file") and str(section.get("source_file")).lower().endswith((".html", ".htm")):
                    refs_for_record.append((f"sections[{index}]", section.get("source_file"), section.get("source_url"), None))
        if refs_for_record:
            records_with_html += 1

        for label, name, declared_url, declared_title in refs_for_record:
            refs += 1
            archive = (ROOT / str(name)).resolve()
            try:
                archive.relative_to(ROOT.resolve())
            except ValueError:
                missing.append(f"{record_rel} {label}: source path escapes repository: {name}")
                continue
            if not archive.is_file():
                missing.append(f"{record_rel} {label}: archived HTML missing: {name}")
                continue
            if archive not in metadata:
                raw = archive.read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                hashes[digest].append(archive.relative_to(ROOT).as_posix())
                parser = MetadataParser()
                try:
                    parser.feed(raw.decode("utf-8-sig", errors="replace"))
                except Exception:
                    pass
                actual_title = re.sub(r"\s+", " ", " ".join(parser.title_parts)).strip()
                metadata[archive] = (actual_title, parser.canonical, digest)
            actual_title, canonical, _ = metadata[archive]
            if declared_title and actual_title and norm(str(declared_title)) not in norm(actual_title) and norm(actual_title) not in norm(str(declared_title)):
                titles.append(f"{record_rel} {label}: source_title={declared_title!r}; archived title={actual_title!r} ({name})")
            if canonical and declared_url and not same_article(str(declared_url), canonical):
                canonicals.append(f"{record_rel} {label}: source_url={declared_url!r}; archived canonical={canonical!r} ({name})")

    duplicate_groups = [paths for paths in hashes.values() if len(paths) > 1]
    print(f"Product records scanned: {count}")
    print(f"Records referencing HTML archives: {records_with_html}")
    print(f"HTML source references inspected (record + section): {refs}")
    print(f"Unique HTML archives inspected: {len(metadata)}")
    print(f"Missing/out-of-repository archives: {len(missing)}")
    print(f"Source-title mismatches: {len(titles)}")
    print(f"Canonical URL mismatches: {len(canonicals)}")
    print(f"Groups of byte-identical HTML archives: {len(duplicate_groups)}")
    for item in missing + titles + canonicals:
        print("WARNING: " + item)
    for group in duplicate_groups:
        print("DUPLICATE ARCHIVE: " + " | ".join(group))
    if args.strict and (missing or titles or canonicals):
        print("RESULT: FAILED")
        return 1
    print("RESULT: DIAGNOSTIC AUDIT COMPLETE (warnings need review; no factual verification implied)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
