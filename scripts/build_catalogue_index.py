#!/usr/bin/env python3
"""Generate the machine-readable TechSpecs product catalogue index.

The index is written to data/catalogue.json so it is published at
https://data.techspecs.dev/catalogue.json when Cloudflare Pages publishes data/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
OUTPUT = DATA_ROOT / "catalogue.json"
BASE_URL = "https://data.techspecs.dev"


def text_value(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def build_entry(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("top-level JSON value must be an object")

    product = record.get("product") if isinstance(record.get("product"), dict) else {}
    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    relative_path = path.relative_to(DATA_ROOT).as_posix()
    record_path = relative_path

    entry: dict[str, Any] = {
        "record_id": record_path.removesuffix(".json"),
        "path": record_path,
        "url": f"{BASE_URL}/{record_path}",
        "schema_version": text_value(record.get("schema_version")),
        "brand": text_value(product.get("brand")),
        "category": text_value(product.get("category")),
        "family": text_value(product.get("family")),
        "model": text_value(product.get("model")),
        "model_slug": text_value(product.get("model_slug") or product.get("slug")),
        "model_year": product.get("model_year") if isinstance(product.get("model_year"), int) else None,
        "year_introduced": product.get("year_introduced") if isinstance(product.get("year_introduced"), int) else None,
        "variant": text_value(product.get("variant")),
        "source": {
            "source_type": text_value(source.get("source_type")),
            "publisher": text_value(source.get("publisher")),
            "source_url": text_value(source.get("source_url")),
            "verification_status": text_value(source.get("verification_status")),
            "checked_at": text_value(source.get("checked_at")),
        },
    }
    return entry


def main() -> int:
    if not DATA_ROOT.is_dir():
        print("ERROR: data/ directory not found", file=sys.stderr)
        return 1

    files = sorted(
        path for path in DATA_ROOT.rglob("*.json")
        if path != OUTPUT and path.name != "catalogue.json"
    )
    entries: list[dict[str, Any]] = []

    for path in files:
        try:
            entries.append(build_entry(path))
        except Exception as exc:
            print(f"ERROR: cannot index {path.relative_to(ROOT)}: {exc}", file=sys.stderr)
            return 1

    if not entries:
        print("ERROR: no product records found under data/", file=sys.stderr)
        return 1

    entries.sort(key=lambda item: item["path"])
    catalogue = {
        "catalogue_version": "1.0",
        "title": "TechSpecs Machine-Readable Product Catalogue",
        "description": (
            "An independently structured index of product records. "
            "Manufacturer and other primary sources are cited as evidence; "
            "TechSpecs defines the record identifiers, normalized data model and discovery interface."
        ),
        "purpose": "machine_reading",
        "canonical_host": BASE_URL,
        "record_count": len(entries),
        "records": entries,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {OUTPUT.relative_to(ROOT)} with {len(entries)} product records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
