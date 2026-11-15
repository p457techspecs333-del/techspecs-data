#!/usr/bin/env python3
"""Slim Samsung comparison ingestion from official Samsung Ireland HTML.

This crawler never launches a browser. It downloads official category/product
HTML, reads Samsung's server-rendered pdd32 product-spec panel, archives the
original page and creates archival-first TechSpecs V2 records.

Use --discover first. Review the generated inventory's product candidates and
set selected=true only for the products in the slim comparison scope. Then run
--archive. The script deliberately does not guess which product is the newest
or force an Apple/Samsung equivalent.
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
CONFIG = ROOT / "config" / "samsung-slim-source-seeds.json"
INVENTORY = ROOT / "data" / "samsung" / "source-inventory.json"
USER_AGENT = "TechSpecsResearchBot/1.0 (+low-rate product-specification research)"
DELAY = 2.0
TIMEOUT = 45
HOSTS = {"www.samsung.com", "samsung.com"}
SPEC_ROOT = ".pdd32-product-spec"


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IE,en;q=0.9",
    })
    return s


def page_product_identity(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    canonical = soup.find("link", rel="canonical")
    canonical_url = canonical.get("href", "") if canonical else ""
    product = {}
    for node in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(node.string or node.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        nodes = data if isinstance(data, list) else [data]
        for obj in nodes:
            if not isinstance(obj, dict):
                continue
            graph = obj.get("@graph", [])
            if isinstance(graph, list):
                nodes.extend(x for x in graph if isinstance(x, dict))
            types = obj.get("@type", [])
            if isinstance(types, str):
                types = [types]
            if "Product" in types:
                product = obj
                break
        if product:
            break
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    return {
        "title": title,
        "name": product.get("name") or title,
        "sku": product.get("sku"),
        "canonical_url": canonical_url,
        "product_jsonld_found": bool(product),
    }


def extract_spec_sections(html: str) -> tuple[list[dict], dict]:
    """Extract all labelled specification rows from Samsung's product panel."""
    soup = BeautifulSoup(html, "lxml")
    root = soup.select_one(SPEC_ROOT)
    if root is None:
        return [], {}
    sections = []
    normalized = {}
    for item in root.select(".pdd32-product-spec__item"):
        title = item.select_one(".pdd32-product-spec__title")
        heading = title.get_text(" ", strip=True) if title else ""
        if not heading:
            continue
        pairs = []
        values = {}
        for entry in item.select(".pdd32-product-spec__content-item"):
            label_node = entry.select_one(".pdd32-product-spec__content-item-title")
            value_node = entry.select_one(".pdd32-product-spec__content-item-desc")
            label = label_node.get_text(" ", strip=True) if label_node else ""
            value = value_node.get_text(" ", strip=True) if value_node else ""
            if not label and not value:
                continue
            pairs.append(f"{label}: {value}" if label else value)
            if label and value:
                key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
                if key:
                    unit_match = re.search(r"\(([^()]*)\)", label)
                    values[key] = {
                        "value": value,
                        "unit": unit_match.group(1) if unit_match else None,
                        "source_section": heading,
                        "verification_status": "source_transcribed",
                    }
        if pairs:
            sections.append({"heading": heading, "source_text": "\n".join(pairs)})
            section_key = re.sub(r"[^a-z0-9]+", "_", heading.lower()).strip("_")
            normalized[section_key] = values
    return sections, normalized


def allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in HOSTS and parsed.path.startswith("/ie/")


def is_product_detail_url(url: str) -> bool:
    """Recognize Samsung model-code suffixes embedded in PDP URL slugs."""
    path = urlparse(url).path
    return bool(re.search(r"(?:^|[-/])(?:sm-|np|ls|qe|vg|ww|rf|vs|hw|wa)[a-z0-9-]+/?$", path, re.I))


def discover(session_obj: requests.Session, config: dict) -> list[dict]:
    found = {}
    seed_errors = []
    for category in config["categories"]:
        seed = category["listing_url"]
        try:
            response = session_obj.get(seed, timeout=TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as exc:
            seed_errors.append({"category": category["category"], "listing_url": seed, "error": str(exc)})
            time.sleep(DELAY)
            continue
        soup = BeautifulSoup(response.text, "lxml")
        links = {urljoin(seed, a["href"]).split("#", 1)[0] for a in soup.find_all("a", href=True)}
        for url in sorted(links):
            if not allowed_url(url):
                continue
            # Product detail URLs on Samsung IE normally carry a model/SKU slug.
            if not is_product_detail_url(url):
                continue
            if url.rstrip("/") == urlparse(seed).path.rstrip("/"):
                continue
            found[url] = {
                "category": category["category"],
                "family": category["family"],
                "listing_source": seed,
                "source_url": url,
                "selected": False,
                "selection_note": "Candidate discovered from official Samsung Ireland category page; select only if current and genuinely comparable.",
            }
        time.sleep(DELAY)
    candidates_by_model = {}
    for item in found.values():
        try:
            response = session_obj.get(item["source_url"], timeout=TIMEOUT)
            response.raise_for_status()
            identity = page_product_identity(response.text)
            if not identity["product_jsonld_found"]:
                continue
            item.update(identity)
            # Collapse colour/storage/carrier SKU pages into one product model.
            # Keep the first canonical model page and retain the other URLs as
            # variant evidence in the inventory rather than creating duplicate records.
            model_key = (item["category"], re.sub(r"\s+", " ", identity["name"]).strip().casefold())
            if model_key not in candidates_by_model:
                item["variant_source_urls"] = []
                candidates_by_model[model_key] = item
            else:
                candidates_by_model[model_key]["variant_source_urls"].append(item["source_url"])
        except requests.RequestException as exc:
            item["discovery_error"] = str(exc)
        time.sleep(DELAY)
    candidates = sorted(candidates_by_model.values(), key=lambda x: (x["category"], x.get("name", ""), x["source_url"]))
    for item in candidates:
        item["seed_errors"] = seed_errors
    return candidates


def archive_one(session_obj: requests.Session, item: dict) -> dict:
    url = item["source_url"]
    response = session_obj.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    if "text/html" not in response.headers.get("Content-Type", "").lower():
        raise ValueError("not an HTML response")
    final_url = response.url
    if not allowed_url(final_url):
        raise ValueError(f"redirected outside Samsung Ireland: {final_url}")
    identity = page_product_identity(response.text)
    if not identity["product_jsonld_found"]:
        raise ValueError("Product JSON-LD not present; refusing to create a product record")
    sections, normalized = extract_spec_sections(response.text)
    if not sections:
        raise ValueError("Samsung product specification panel not found in server-rendered HTML")
    # Model-level slug: do not create one product record per colour/storage SKU.
    slug = re.sub(r"[^a-z0-9]+", "-", identity["name"].lower()).strip("-")
    slug = slug[:100] or "samsung-product"
    category = item["category"]
    source_dir = ROOT / "sources" / "samsung" / category
    data_dir = ROOT / "data" / "samsung" / category
    source_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    source_path = source_dir / f"{slug}.html"
    record_path = data_dir / f"{slug}.json"
    source_path.write_text(response.text, encoding="utf-8")
    source_rel = source_path.relative_to(ROOT).as_posix()
    record = {
        "schema_version": "2.0",
        "product": {
            "brand": "Samsung",
            "category": category,
            "family": item["family"],
            "model": identity["name"],
            "model_slug": slug,
            "model_numbers": [identity["sku"]] if identity.get("sku") else [],
        },
        "source": {
            "source_type": "manufacturer",
            "source_url": identity["canonical_url"] or final_url,
            "source_file": source_rel,
            "source_title": identity["title"],
            "publisher": "Samsung Electronics",
            "published_at": None,
            "checked_at": today(),
            "verification_status": "url_checked",
            "verification_notes": "Official Samsung Ireland product page archived. Extracted fields are source-transcribed, not independently field-verified.",
            "notes": ["Original HTML retained as source evidence.", "Model variants and retailer configurations are not separate records unless they are distinct products."],
        },
        "extraction": {
            "method": "structured_extraction",
            "normalization_status": "partially_normalized",
            "note": "Server-rendered Samsung product specification rows transcribed from pdd32-product-spec markup. Field-level verification remains outstanding.",
            "extracted_at": today(),
            "reviewed_at": None,
        },
        "sections": [
            {
                "heading": section["heading"],
                "source_text": section["source_text"],
                "source_url": identity["canonical_url"] or final_url,
                "source_file": source_rel,
            }
            for section in sections
        ],
        "normalized_specifications": normalized,
        "record_notes": [
            "Generated by scripts/samsung_slim_ingest.py.",
            "Specification labels are preserved as Samsung presents them; field names are normalized mechanically from labels.",
            "No Apple/Samsung equivalence is asserted by this product record.",
        ],
    }
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"source_file": source_rel, "record_path": record_path.relative_to(ROOT).as_posix(), "section_count": len(sections), "field_count": sum(len(v) for v in normalized.values())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--discover", action="store_true")
    group.add_argument("--archive", action="store_true")
    args = parser.parse_args()
    if not CONFIG.is_file():
        print(f"Missing seed config: {CONFIG}", file=sys.stderr)
        return 2
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    s = session()
    try:
        if args.discover:
            items = discover(s, config)
            INVENTORY.parent.mkdir(parents=True, exist_ok=True)
            INVENTORY.write_text(json.dumps({
                "inventory_version": "1.0",
                "purpose": "slim_samsung_comparison",
                "market": "Ireland",
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "scope_note": "Candidate list only. Select current models and genuine Apple counterparts manually; do not infer equivalence from discovery order.",
                "candidates": items,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Discovered {len(items)} official Samsung product candidates.")
            print(f"Review and mark selected=true in {INVENTORY.relative_to(ROOT)} before --archive.")
            return 0
        if not INVENTORY.is_file():
            print("Run --discover first.", file=sys.stderr)
            return 2
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        selected = [x for x in inventory.get("candidates", []) if x.get("selected") is True and x.get("archive_status") != "archived_with_specs"]
        if not selected:
            print("No candidates selected. Mark only the intended slim-scope products selected=true in the inventory.", file=sys.stderr)
            return 0
        failures = []
        success = 0
        for item in selected:
            try:
                result = archive_one(s, item)
                item["archive_result"] = result
                item["archive_status"] = "archived_with_specs"
                success += 1
                print(f"[OK] {item.get('name')}: {result['field_count']} fields / {result['section_count']} sections")
            except Exception as exc:
                item["archive_status"] = "failed"
                item["archive_error"] = str(exc)
                failures.append((item.get("name", item["source_url"]), str(exc)))
                print(f"[SKIP] {item.get('name', item['source_url'])}: {exc}")
            time.sleep(DELAY)
        INVENTORY.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Archived {success}; failed {len(failures)}.")
        return 0 if success else 1
    except requests.RequestException as exc:
        print(f"Samsung request failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
