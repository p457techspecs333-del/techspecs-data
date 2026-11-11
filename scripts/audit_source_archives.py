#!/usr/bin/env python3
"""Diagnose whether product records agree with their archived HTML source metadata."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
DATA_ROOT=ROOT/"data"
SKIP={"catalogue.json","api-manifest.json","generation-report.json","source-inventory.json"}
class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.in_title=False; self.title_parts=[]; self.canonical=None
    def handle_starttag(self,tag,attrs):
        a={k.lower():v for k,v in attrs}
        if tag.lower()=="title": self.in_title=True
        if tag.lower()=="link" and (a.get("rel") or "").lower()=="canonical": self.canonical=a.get("href")
    def handle_endtag(self,tag):
        if tag.lower()=="title": self.in_title=False
    def handle_data(self,data):
        if self.in_title: self.title_parts.append(data)
def norm(s):
    s=re.sub(r"\s+"," ",s or "").strip().casefold()
    return re.sub(r"\s*[-–|]\s*apple support(?:\s*\([^)]*\))?$","",s)
def same_article(a,b):
    if not a or not b: return True
    pa,pb=urlparse(a),urlparse(b)
    if pa.hostname!=pb.hostname: return False
    if pa.hostname and pa.hostname.lower().endswith("apple.com"):
        aa=[p for p in pa.path.split("/") if p]; bb=[p for p in pb.path.split("/") if p]
        return bool(aa and bb and aa[-1]==bb[-1])
    return pa.path.rstrip("/")==pb.path.rstrip("/")
def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--strict",action="store_true"); args=ap.parse_args()
    count=refs=0; metadata={}; titles=[]; canonicals=[]; missing=[]; hashes=defaultdict(list)
    for p in sorted(DATA_ROOT.rglob("*.json")):
        if p.name in SKIP or "schemas" in p.relative_to(DATA_ROOT).parts: continue
        try: rec=json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        if not isinstance(rec,dict): continue
        count+=1; src=rec.get("source") if isinstance(rec.get("source"),dict) else {}; name=src.get("source_file")
        if not name or not str(name).lower().endswith((".html",".htm")): continue
        refs+=1; archive=(ROOT/str(name)).resolve()
        try: archive.relative_to(ROOT.resolve())
        except ValueError: missing.append(f"{p.relative_to(ROOT)}: source path escapes repository: {name}"); continue
        if not archive.is_file(): missing.append(f"{p.relative_to(ROOT)}: archived HTML missing: {name}"); continue
        if archive not in metadata:
            raw=archive.read_bytes(); digest=hashlib.sha256(raw).hexdigest(); hashes[digest].append(archive.relative_to(ROOT).as_posix())
            parser=MetadataParser()
            try: parser.feed(raw.decode("utf-8-sig",errors="replace"))
            except Exception: pass
            metadata[archive]=(re.sub(r"\s+"," "," ".join(parser.title_parts)).strip(),parser.canonical,digest)
        actual,canonical,_=metadata[archive]; declared=src.get("source_title")
        if declared and actual and norm(str(declared)) not in norm(actual) and norm(actual) not in norm(str(declared)):
            titles.append(f"{p.relative_to(ROOT)}: source_title={declared!r}; archived title={actual!r} ({name})")
        url=src.get("source_url")
        if canonical and url and not same_article(str(url),canonical):
            canonicals.append(f"{p.relative_to(ROOT)}: source_url={url!r}; archived canonical={canonical!r} ({name})")
    dup=[v for v in hashes.values() if len(v)>1]
    print(f"Product records scanned: {count}")
    print(f"Records referencing HTML archives: {refs}")
    print(f"Unique HTML archives inspected: {len(metadata)}")
    print(f"Missing/out-of-repository archives: {len(missing)}")
    print(f"Source-title mismatches: {len(titles)}")
    print(f"Canonical URL mismatches: {len(canonicals)}")
    print(f"Groups of byte-identical HTML archives: {len(dup)}")
    for item in missing+titles+canonicals: print("WARNING: "+item)
    for group in dup: print("DUPLICATE ARCHIVE: "+" | ".join(group))
    if args.strict and (missing or titles or canonicals): print("RESULT: FAILED"); return 1
    print("RESULT: DIAGNOSTIC AUDIT COMPLETE (warnings need review; no factual verification implied)")
    return 0
if __name__=="__main__": sys.exit(main())
