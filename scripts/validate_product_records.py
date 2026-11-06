#!/usr/bin/env python3
"""Audit product JSON records and validate any records using schema v2.

Default mode is deliberately migration-safe: legacy records are audited for
basic integrity, while records declaring schema_version 2.0 are also checked
against schemas/product-record-v2.schema.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
SCHEMA_PATH = ROOT / "schemas" / "product-record-v2.schema.json"
CATALOGUE_PATH = DATA_ROOT / "catalogue.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict-v2",
        action="store_true",
        help="require every product record to validate against schema v2",
    )
    args = parser.parse_args()

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("ERROR: missing dependency. Install with: python -m pip install -r requirements.txt")
        return 2

    if not SCHEMA_PATH.is_file():
        print(f"ERROR: schema not found: {SCHEMA_PATH.relative_to(ROOT)}")
        return 2

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    except Exception as exc:
        print(f"ERROR: schema is invalid: {exc}")
        return 2

    # catalogue.json is a discovery document, not a product record.
    files = sorted(
        path for path in DATA_ROOT.rglob("*.json")
        if path != CATALOGUE_PATH and path.name != "catalogue.json" and "schemas" not in path.relative_to(DATA_ROOT).parts
    ) if DATA_ROOT.exists() else []
    if not files:
        print("ERROR: no product JSON files found under data/")
        return 1

    source_files = {p.name for p in (ROOT / "sources").rglob("*.md")} if (ROOT / "sources").exists() else set()
    errors: list[str] = []
    warnings: list[str] = []
    versions: Counter[str] = Counter()
    validated_v2 = 0

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rel}: invalid JSON ({exc})")
            continue

        if not isinstance(record, dict):
            errors.append(f"{rel}: top-level JSON value must be an object")
            continue

        version = str(record.get("schema_version", "legacy/unspecified"))
        versions[version] += 1
        product = record.get("product") if isinstance(record.get("product"), dict) else {}
        slug = product.get("model_slug") or product.get("slug")
        if slug and str(slug) != path.stem:
            errors.append(f"{rel}: product slug {slug!r} does not match filename {path.stem!r}")
        elif not slug:
            warnings.append(f"{rel}: no product.model_slug; filename pairing used")

        if args.strict_v2 or version == "2.0":
            validated_v2 += 1
            for issue in sorted(validator.iter_errors(record), key=lambda e: list(map(str, e.absolute_path))):
                location = ".".join(str(part) for part in issue.absolute_path) or "$"
                errors.append(f"{rel}: schema v2 {location}: {issue.message}")

        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        source_name = source.get("source_file")
        if source_name:
            if Path(str(source_name)).name not in source_files:
                warnings.append(f"{rel}: source_file {source_name!r} was not found under sources/")
        else:
            expected = f"{path.stem}-source.md"
            if expected not in source_files:
                warnings.append(f"{rel}: no matching {expected} found under sources/")

        if not source.get("source_url"):
            warnings.append(f"{rel}: source URL is blank/null; provenance needs review")
        if source.get("verification_status") in (None, "", "not_checked"):
            warnings.append(f"{rel}: source verification status is absent or not_checked")

    print(f"Product records scanned: {len(files)}")
    print("Schema versions: " + ", ".join(f"{key}={value}" for key, value in sorted(versions.items())))
    print(f"Records checked against v2 schema: {validated_v2}")
    print(f"Errors: {len(errors)} | Warnings: {len(warnings)}")

    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARNING: {item}")

    if errors:
        print("RESULT: FAILED")
        return 1
    print("RESULT: PASSED (warnings identify review work; they do not certify factual accuracy)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
