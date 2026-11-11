#!/usr/bin/env python3
"""Smoke-test the deployed TechSpecs machine-readable data host."""
from __future__ import annotations
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

BASE = "https://data.techspecs.dev"
USER_AGENT = "TechSpecs-Live-Smoke-Test/1.0"
ATTEMPTS = 12
RETRY_SECONDS = 10

def get(url: str):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "data.techspecs.dev":
        raise RuntimeError(f"Refusing to fetch non-canonical TechSpecs host: {url}")
    last_error = None
    for attempt in range(ATTEMPTS):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urlopen(request, timeout=20) as response:
                status = response.status
                body = response.read()
                content_type = response.headers.get("Content-Type", "")
            if status != 200:
                raise RuntimeError(f"HTTP {status} for {url}")
            return body, content_type
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt + 1 < ATTEMPTS:
                print(f"Attempt {attempt + 1}/{ATTEMPTS} failed for {url}: {exc}; retrying in {RETRY_SECONDS}s")
                time.sleep(RETRY_SECONDS)
    raise RuntimeError(f"Live endpoint failed after {ATTEMPTS} attempts: {url}: {last_error}")

def get_json(url: str):
    body, content_type = get(url)
    try:
        return json.loads(body.decode("utf-8")), content_type
    except Exception as exc:
        raise RuntimeError(f"Endpoint did not return valid UTF-8 JSON: {url}: {exc}") from exc

def main() -> int:
    manifest, manifest_type = get_json(BASE + "/api-manifest.json")
    if not isinstance(manifest, dict) or str(manifest.get("interface_version")) != "1.0":
        raise RuntimeError("API manifest missing or has unexpected interface_version")
    if manifest.get("canonical_data_host") != BASE:
        raise RuntimeError("API manifest canonical_data_host does not match data.techspecs.dev")
    print(f"PASS manifest: interface_version={manifest['interface_version']} content_type={manifest_type}")

    catalogue, catalogue_type = get_json(BASE + "/catalogue.json")
    records = catalogue.get("records") if isinstance(catalogue, dict) else None
    if not isinstance(records, list) or not records:
        raise RuntimeError("Catalogue has no records array or is empty")
    if catalogue.get("record_count") != len(records):
        raise RuntimeError(f"Catalogue record_count={catalogue.get('record_count')} but records length={len(records)}")
    ids = [entry.get("record_id") for entry in records if isinstance(entry, dict)]
    urls = [entry.get("url") for entry in records if isinstance(entry, dict)]
    if len(ids) != len(records) or len(set(ids)) != len(ids):
        raise RuntimeError("Catalogue has malformed or duplicate record IDs")
    if len(urls) != len(records) or len(set(urls)) != len(urls):
        raise RuntimeError("Catalogue has malformed or duplicate product URLs")
    by_id = {entry["record_id"]: entry for entry in records}
    print(f"PASS catalogue: {len(records)} unique product records content_type={catalogue_type}")

    samples = {
        "apple/iphone/iphone-17": "iphone-17",
        "apple/ipod/ipod-touch-7th-generation": "ipod-touch-7th-generation",
        "apple/watch/apple-watch-series-1": "apple-watch-series-1",
    }
    for record_id, expected_slug in samples.items():
        entry = by_id.get(record_id)
        if not entry:
            raise RuntimeError(f"Expected smoke-test record is absent from catalogue: {record_id}")
        record, content_type = get_json(entry["url"])
        product = record.get("product") if isinstance(record, dict) else None
        if not isinstance(product, dict):
            raise RuntimeError(f"Product endpoint returned no product object: {entry['url']}")
        if product.get("model_slug") != expected_slug:
            raise RuntimeError(f"Product URL resolved to unexpected model: {entry['url']} -> {product.get('model_slug')!r}")
        if product.get("brand") != "Apple":
            raise RuntimeError(f"Unexpected brand in product endpoint: {entry['url']}")
        print(f"PASS product route: {record_id} -> {entry['url']} content_type={content_type}")

    print("RESULT: LIVE DATA HOST SMOKE TEST PASSED")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"RESULT: LIVE DATA HOST SMOKE TEST FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
