#!/usr/bin/env python3
"""Discover and check official Apple Ireland URLs for existing iPhone records.

This script is deliberately non-destructive:
- reads the generated product catalogue;
- searches only for iPhone records;
- uses Google Programmable Search JSON API (no search-page scraping);
- accepts candidate URLs only from official Apple Ireland hosts;
- checks candidate pages and records evidence;
- writes a separate review file; it never edits product JSON records.

Environment:
  GOOGLE_CSE_API_KEY  Google Programmable Search API key
  GOOGLE_CSE_CX       Programmable Search Engine ID configured to search the web

Example:
  python scripts/discover_apple_iphone_urls.py --limit 5
  python scripts/discover_apple_iphone_urls.py --model "iPhone 17 Pro"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "data" / "catalogue.json"
DEFAULT_OUTPUT = ROOT / "sources" / "apple" / "iphone" / "url-discovery-candidates.json"
SEARCH_ENDPOINT = "https://www.googleapis.com/customsearch/v1"
ALLOWED_HOSTS = {"support.apple.com", "apple.com", "www.apple.com", "images.apple.com"}
USER_AGENT = "TechSpecsURLDiscovery/1.0 (research; contact: repository-maintainer)"


class PageTitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.parts.append(data)


def is_official_apple_ireland_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    if parsed.scheme != "https" or host not in ALLOWED_HOSTS:
        return False
    if host == "support.apple.com":
        return path.startswith("/en-ie/")
    if host in {"apple.com", "www.apple.com", "images.apple.com"}:
        return path.startswith("/ie/")
    return False


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def search_apple_urls(model: str, api_key: str, cx: str, max_results: int) -> list[dict]:
    query = f'"{model}" (site:support.apple.com/en-ie OR site:apple.com/ie) ("Tech Specs" OR specifications OR support)'
    params = urlencode({"key": api_key, "cx": cx, "q": query, "num": max_results})
    request = Request(
        f"{SEARCH_ENDPOINT}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("items", [])


def check_candidate(url: str, model: str) -> dict:
    result = {
        "url": url,
        "http_status": None,
        "final_url": None,
        "page_title": None,
        "model_name_found": False,
        "check_status": "needs_review",
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    if not is_official_apple_ireland_url(url):
        result["check_status"] = "rejected_not_official_apple_ireland"
        return result

    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=25) as response:
            body = response.read(2_000_000).decode("utf-8", errors="replace")
            result["http_status"] = response.status
            result["final_url"] = response.geturl()
        parser = PageTitleParser()
        parser.feed(body)
        title = " ".join(" ".join(parser.parts).split())
        result["page_title"] = title or None
        model_norm = normalize(model)
        haystack = normalize(title + " " + body[:500_000])
        result["model_name_found"] = bool(model_norm and model_norm in haystack)
        if result["http_status"] == 200 and is_official_apple_ireland_url(result["final_url"]) and result["model_name_found"]:
            result["check_status"] = "url_checked_model_name_found"
        elif result["http_status"] == 200 and is_official_apple_ireland_url(result["final_url"]):
            result["check_status"] = "url_reachable_needs_model_review"
        else:
            result["check_status"] = "redirected_or_unavailable_needs_review"
    except HTTPError as exc:
        result["http_status"] = exc.code
        result["check_status"] = "http_error_needs_review"
    except (URLError, TimeoutError, OSError, UnicodeError) as exc:
        result["check_status"] = f"fetch_error:{type(exc).__name__}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="Run discovery for one exact catalogue model name.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of iPhone records (0 = all).")
    parser.add_argument("--max-results", type=int, default=10, choices=range(1, 11))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between search requests.")
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cx = os.getenv("GOOGLE_CSE_CX")
    if not api_key or not cx:
        print("ERROR: set GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX before running.", file=sys.stderr)
        print("Use a Google Programmable Search Engine configured for web-wide search.", file=sys.stderr)
        return 2
    if not CATALOGUE.is_file():
        print(f"ERROR: catalogue not found: {CATALOGUE.relative_to(ROOT)}", file=sys.stderr)
        return 2

    try:
        catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read catalogue: {exc}", file=sys.stderr)
        return 2

    records = [
        item for item in catalogue.get("records", [])
        if item.get("brand") == "Apple"
        and item.get("family") == "iPhone"
        and item.get("category") == "smartphone"
    ]
    if args.model:
        wanted = normalize(args.model)
        records = [item for item in records if normalize(item.get("model", "")) == wanted]
        if not records:
            print(f"ERROR: no exact iPhone model match in catalogue: {args.model}", file=sys.stderr)
            return 1
    if args.limit > 0:
        records = records[:args.limit]

    output_records = []
    for index, record in enumerate(records):
        model = record["model"]
        entry = {
            "record_id": record["record_id"],
            "model": model,
            "existing_source_url": (record.get("source") or {}).get("source_url"),
            "existing_verification_status": (record.get("source") or {}).get("verification_status"),
            "discovery_query_scope": "official Apple Ireland only",
            "candidates": [],
        }
        try:
            search_items = search_apple_urls(model, api_key, cx, args.max_results)
            seen: set[str] = set()
            for item in search_items:
                link = item.get("link", "")
                if not link or link in seen or not is_official_apple_ireland_url(link):
                    continue
                seen.add(link)
                checked = check_candidate(link, model)
                checked["search_title"] = item.get("title")
                checked["search_snippet"] = item.get("snippet")
                entry["candidates"].append(checked)
        except HTTPError as exc:
            entry["search_error"] = f"Google CSE HTTP {exc.code}"
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            entry["search_error"] = f"{type(exc).__name__}: {exc}"
        output_records.append(entry)
        print(f"[{index + 1}/{len(records)}] {model}: {len(entry['candidates'])} official Apple Ireland candidate(s)")
        if index + 1 < len(records):
            time.sleep(max(0.0, args.delay))

    document = {
        "document_type": "techspecs_apple_iphone_url_discovery",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalogue_source": "data/catalogue.json",
        "search_provider": "Google Programmable Search JSON API",
        "scope": "Apple iPhone records only; official Apple Ireland URLs only",
        "note": "Candidates are research leads. A reachable URL and model-name match do not certify every specification on the page. No product records are modified.",
        "record_count": len(output_records),
        "records": output_records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved {len(output_records)} discovery records to {args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output}")
    print("Existing product JSON files were not changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
