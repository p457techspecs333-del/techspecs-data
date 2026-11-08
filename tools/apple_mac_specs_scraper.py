#!/usr/bin/env python3
"""Collect Apple's official Mac model-index and Technical Specifications pages.

The run is deliberately best-effort: Apple Support sometimes rate-limits cloud
runners. Every requested URL, HTTP status, redirect and failure is recorded so
a partial run is never mislabeled complete.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

OUT = Path("apple_mac_extraction")
HTML = OUT / "original_html"
SPECS = OUT / "technical_specs_html"
HTML.mkdir(parents=True, exist_ok=True)
SPECS.mkdir(parents=True, exist_ok=True)

FAMILIES = {
    "macbook_air": "https://support.apple.com/en-ie/102869",
    "macbook_pro": "https://support.apple.com/en-ie/108052",
    "macbook": "https://support.apple.com/en-ie/103257",
    "imac": "https://support.apple.com/en-ie/108054",
    "mac_mini": "https://support.apple.com/en-ie/102852",
    "mac_studio": "https://support.apple.com/en-ie/102231",
    "mac_pro": "https://support.apple.com/en-ie/102887",
}
COMPARE_URL = "https://www.apple.com/ie/mac/compare/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IE,en;q=0.9,en-GB;q=0.8",
    "Cache-Control": "no-cache",
}
session = requests.Session()
session.headers.update(HEADERS)
report = {
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "sources": [],
    "model_index_pages": [],
    "technical_spec_pages": [],
    "errors": [],
    "notes": [
        "Official Apple pages only are saved as source HTML.",
        "HTTP 429/403 pages are recorded as failures, not treated as successful captures.",
        "A successful index scrape is not proof that every historic model has been captured."
    ],
}

def safe_name(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9._-]+", "_", text).strip("_.-")
    return (text[:100] or "apple_page")

def get_page(url: str, tries: int = 4):
    last = None
    for attempt in range(tries):
        try:
            response = session.get(url, timeout=35)
            last = response
            if response.status_code == 200 and "<html" in response.text[:5000].lower():
                return response
            if response.status_code not in (429, 500, 502, 503, 504):
                break
        except requests.RequestException as exc:
            report["errors"].append({"url": url, "error": str(exc), "attempt": attempt + 1})
        if attempt < tries - 1:
            time.sleep(min(3 * (2 ** attempt), 18))
    return last

def is_apple_url(url: str) -> bool:
    p = urlparse(url)
    return p.scheme == "https" and (p.hostname or "").lower() in {
        "support.apple.com", "www.apple.com", "apple.com"
    }

def save_response(response, folder: Path, stem: str):
    final_url = response.url
    path = folder / (safe_name(stem) + ".html")
    path.write_text(response.text, encoding="utf-8")
    return {"requested_url": response.request.url, "final_url": final_url,
            "status": response.status_code, "title": BeautifulSoup(response.text, "html.parser").title.get_text(" ", strip=True) if BeautifulSoup(response.text, "html.parser").title else "",
            "saved_file": str(path), "bytes": len(response.content)}

# Capture Apple comparison page as an additional discovery source.
urls_to_check = [("mac_compare", COMPARE_URL)]
urls_to_check.extend(FAMILIES.items())
for name, url in urls_to_check:
    response = get_page(url)
    item = {"family": name, "requested_url": url}
    if response is None:
        item.update({"status": None, "error": "No HTTP response"})
        report["model_index_pages"].append(item)
        continue
    item["status"] = response.status_code
    item["final_url"] = response.url
    if response.status_code == 200 and "<html" in response.text[:5000].lower():
        saved = save_response(response, HTML, name)
        item.update(saved)
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = urljoin(response.url, a["href"])
            label = " ".join(a.get_text(" ", strip=True).split())
            if is_apple_url(href) and (
                re.search(r"tech\s*spec|technical\s*specification", label, re.I)
                or re.search(r"/\d{5,6}$", urlparse(href).path)
            ):
                links.append({"label": label, "url": href})
        # Keep first occurrence of each URL while preserving source order.
        seen = set()
        item["discovered_links"] = [x for x in links if not (x["url"] in seen or seen.add(x["url"]))]
        report["sources"].append(saved)
    else:
        item["error"] = f"Apple returned HTTP {response.status_code}; index not saved as source HTML."
        report["errors"].append({"url": url, "status": response.status_code})
    report["model_index_pages"].append(item)
    time.sleep(1.0)

# Follow only explicit Apple Tech Specs links found in the family index pages.
seen_specs = set()
for index in report["model_index_pages"]:
    for link in index.get("discovered_links", []):
        url = link["url"]
        if url in seen_specs:
            continue
        seen_specs.add(url)
        response = get_page(url, tries=3)
        record = {"label": link.get("label", ""), "requested_url": url}
        if response is None:
            record.update({"status": None, "error": "No HTTP response"})
        else:
            record["status"] = response.status_code
            record["final_url"] = response.url
            if response.status_code == 200 and "<html" in response.text[:5000].lower():
                saved = save_response(response, SPECS, safe_name(urlparse(response.url).path.split("/")[-1] or link.get("label", "spec")))
                record.update(saved)
                report["sources"].append(saved)
            else:
                record["error"] = f"Apple returned HTTP {response.status_code}; page not saved."
                report["errors"].append({"url": url, "status": response.status_code})
        report["technical_spec_pages"].append(record)
        time.sleep(1.0)

report["finished_utc"] = datetime.now(timezone.utc).isoformat()
report["summary"] = {
    "index_pages_requested": len(urls_to_check),
    "index_pages_saved": sum(1 for x in report["model_index_pages"] if x.get("saved_file")),
    "unique_tech_specs_urls_discovered": len(seen_specs),
    "tech_specs_pages_saved": sum(1 for x in report["technical_spec_pages"] if x.get("saved_file")),
    "failed_or_rate_limited": len(report["errors"]),
}
(OUT / "extraction_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
(OUT / "discovered_urls.json").write_text(json.dumps({
    "model_indexes": [{"family": x.get("family"), "url": x.get("requested_url"), "status": x.get("status")} for x in report["model_index_pages"]],
    "technical_specs": report["technical_spec_pages"],
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(report["summary"], indent=2))
print(f"Report: {OUT / 'extraction_report.json'}")
