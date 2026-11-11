#!/usr/bin/env python3
"""Archive official Apple HTML sources listed in source-archive-requests/*.json.

Only Apple-owned web hosts are accepted. The original response bytes are saved
unchanged; a sidecar JSON records the requested/final/canonical URLs, page title,
capture time and SHA-256. Existing unchanged archives are not fetched again.
"""
from __future__ import annotations
import hashlib, json, sys, time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_HOSTS = {"support.apple.com", "apple.com", "www.apple.com"}
DEFAULT_REQUEST_DIR = ROOT / "source-archive-requests"

class PageMetadata(HTMLParser):
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

def allowed(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in ALLOWED_HOSTS

def fetch(url: str):
    last_error = None
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "TechSpecs-SourceArchive/1.0 (+https://github.com/p457techspecs333-del/techspecs-data)"})
            with urlopen(request, timeout=45) as response:
                final_url = response.geturl()
                if not allowed(final_url):
                    raise ValueError(f"redirected to a non-allowlisted host: {final_url}")
                raw = response.read()
                content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower() and b"<html" not in raw[:4096].lower():
                raise ValueError(f"response does not appear to be HTML (Content-Type: {content_type})")
            parser = PageMetadata()
            parser.feed(raw.decode("utf-8-sig", errors="replace"))
            title = " ".join(" ".join(parser.title_parts).split())
            if not title:
                raise ValueError("HTML response has no title")
            if parser.canonical and not allowed(parser.canonical):
                raise ValueError(f"canonical URL is outside allowlisted Apple hosts: {parser.canonical}")
            return raw, final_url, parser.canonical, title, content_type
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
        except Exception:
            raise
    raise RuntimeError(f"could not fetch {url}: {last_error}")

def main() -> int:
    request_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_REQUEST_DIR
    if not request_dir.is_dir():
        print(f"ERROR: request directory not found: {request_dir}")
        return 2
    requests = sorted(request_dir.rglob("*.json"))
    if not requests:
        print("ERROR: no source archive request JSON files found")
        return 2
    archived = skipped = 0
    for request_file in requests:
        try:
            request_doc = json.loads(request_file.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"ERROR: invalid request file {request_file.relative_to(ROOT)}: {exc}")
            return 2
        sources = request_doc.get("sources") if isinstance(request_doc, dict) else None
        if not isinstance(sources, list):
            print(f"ERROR: {request_file.relative_to(ROOT)} must contain a sources array")
            return 2
        for item in sources:
            if not isinstance(item, dict):
                print(f"ERROR: non-object source request in {request_file.relative_to(ROOT)}")
                return 2
            url = str(item.get("url") or "").strip()
            expected = str(item.get("expected_title_contains") or "").strip().casefold()
            relative = Path(str(item.get("output_path") or ""))
            if not allowed(url):
                print(f"ERROR: source URL is not HTTPS on an allowlisted Apple host: {url}")
                return 2
            if not expected:
                print(f"ERROR: expected_title_contains is required for {url}")
                return 2
            if relative.is_absolute() or ".." in relative.parts or not str(relative).startswith("apple_remaining_extraction/technical_specs_html/") or relative.suffix.lower() not in {".html", ".htm"}:
                print(f"ERROR: output_path must be an HTML file under apple_remaining_extraction/technical_specs_html/: {relative}")
                return 2
            output = (ROOT / relative).resolve()
            try:
                output.relative_to(ROOT.resolve())
            except ValueError:
                print(f"ERROR: output path escapes repository: {relative}")
                return 2
            metadata_path = output.with_suffix(output.suffix + ".metadata.json")
            if output.is_file() and metadata_path.is_file() and not item.get("refresh", False):
                try:
                    old = json.loads(metadata_path.read_text(encoding="utf-8"))
                    if old.get("requested_url") == url:
                        print(f"SKIP {relative}: archive already exists for this URL")
                        skipped += 1
                        continue
                except Exception:
                    pass
            raw, final_url, canonical, title, content_type = fetch(url)
            if expected not in title.casefold():
                raise RuntimeError(f"title check failed for {url}: expected {expected!r} within {title!r}")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(raw)
            metadata = {
                "requested_url": url,
                "final_url": final_url,
                "canonical_url": canonical,
                "page_title": title,
                "publisher": "Apple",
                "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                "content_type": content_type,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "archive_path": relative.as_posix(),
                "request_file": request_file.relative_to(ROOT).as_posix(),
            }
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"ARCHIVED {relative}: {title} [{metadata['sha256']}]")
            archived += 1
    print(f"Source pages archived: {archived}; already archived/skipped: {skipped}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
