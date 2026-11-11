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
from urllib.parse import urlparse

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

    # Only product records belong in the product validator. Inventory and
    # generation-report JSON files are supporting metadata, not products.
    non_product_filenames = {
        "catalogue.json",
        "api-manifest.json",
        "generation-report.json",
        "source-inventory.json",
    }
    files = sorted(
        path for path in DATA_ROOT.rglob("*.json")
        if path != CATALOGUE_PATH
        and path.name not in non_product_filenames
        and "schemas" not in path.relative_to(DATA_ROOT).parts
    ) if DATA_ROOT.exists() else []
    if not files:
        print("ERROR: no product JSON files found under data/")
        return 1

    source_files = {p.name for p in (ROOT / "sources").rglob("*.md")} if (ROOT / "sources").exists() else set()
    errors: list[str] = []
    warnings: list[str] = []
    source_archives_not_retained = 0
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
            # source_file may point to an archived HTML/PDF or other repository
            # asset outside sources/*.md. Validate the actual repository-relative
            # path rather than requiring every provenance file to be Markdown.
            source_path = (ROOT / str(source_name)).resolve()
            try:
                source_path.relative_to(ROOT.resolve())
            except ValueError:
                warnings.append(f"{rel}: source_file {source_name!r} resolves outside the repository")
            else:
                if not source_path.is_file():
                    warnings.append(f"{rel}: source_file {source_name!r} does not exist in the repository")
        else:
            expected = f"{path.stem}-source.md"
            if expected not in source_files:
                if "source_file" in source and source.get("source_file") is None:
                    # Explicit null is a deliberate statement that no archived
                    # source file is retained; report it separately from broken
                    # paths or missing implicit Markdown files.
                    source_archives_not_retained += 1
                else:
                    warnings.append(f"{rel}: no matching {expected} found under sources/")

        # Validate optional section-level provenance introduced in schema v2.
        sections = record.get("sections")
        if isinstance(sections, list):
            for section_index, section in enumerate(sections):
                if not isinstance(section, dict):
                    continue
                section_file = section.get("source_file")
                section_url = str(section.get("source_url") or "").strip()
                section_label = f"{rel}: sections[{section_index}]"
                if bool(section_file) != bool(section_url):
                    warnings.append(
                        f"{section_label}: source_url and source_file should be supplied together"
                    )
                if section_file:
                    section_path = (ROOT / str(section_file)).resolve()
                    try:
                        section_path.relative_to(ROOT.resolve())
                    except ValueError:
                        warnings.append(
                            f"{section_label}: source_file {section_file!r} resolves outside the repository"
                        )
                    else:
                        if not section_path.is_file():
                            warnings.append(
                                f"{section_label}: source_file {section_file!r} does not exist in the repository"
                            )

        source_url = str(source.get("source_url") or "").strip()
        if not source_url:
            warnings.append(f"{rel}: source URL is blank/null; provenance needs review")
        else:
            parsed_source_url = urlparse(source_url)
            host = (parsed_source_url.hostname or "").lower()
            path_part = parsed_source_url.path.lower()
            # Ireland is the target market, but an official Apple technical
            # specification may only be published or indexed under another
            # regional locale. Accept any Apple-owned support/specification
            # URL; records should explain non-Ireland locales in verification_notes.
            is_official_apple_source = (
                host == "support.apple.com"
                or host in {"apple.com", "www.apple.com"}
                or host == "images.apple.com"
            )
            if not is_official_apple_source:
                errors.append(
                    f"{rel}: source URL must be hosted on an official Apple domain "
                    f"(support.apple.com, apple.com, or images.apple.com); "
                    f"found {source_url!r}"
                )
        if source.get("verification_status") in (None, "", "not_checked"):
            warnings.append(f"{rel}: source verification status is absent or not_checked")


    # Cross-check category inventories against product records and archived sources.
    inventory_paths = sorted(p for p in (DATA_ROOT / "apple").glob("*/source-inventory.json") if p.parent.name in {"airpods", "homepod", "ipod", "displays", "accessories", "software"})
    global_slugs: dict[str, list[str]] = {}
    for product_path in files:
        try:
            product_record = json.loads(product_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        product_obj = product_record.get("product") if isinstance(product_record, dict) else {}
        if not isinstance(product_obj, dict):
            continue
        product_slug = product_obj.get("model_slug") or product_obj.get("slug")
        if product_slug:
            global_slugs.setdefault(str(product_slug), []).append(product_path.relative_to(ROOT).as_posix())
    for product_slug, locations in sorted(global_slugs.items()):
        if len(locations) > 1:
            warnings.append(f"duplicate product.model_slug {product_slug!r}: " + ", ".join(locations))

    inventories_checked = 0
    inventory_records_checked = 0
    for inventory_path in inventory_paths:
        inventory_rel = inventory_path.relative_to(ROOT).as_posix()
        try:
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        except Exception as exc:
            warnings.append(f"{inventory_rel}: invalid inventory JSON ({exc})")
            continue
        if not isinstance(inventory, dict):
            warnings.append(f"{inventory_rel}: inventory top-level value is not an object")
            continue
        inventories_checked += 1
        scope = inventory.get("working_scope")
        if not isinstance(scope, list):
            warnings.append(f"{inventory_rel}: working_scope is absent or not an array")
            continue

        category_dir = inventory_path.parent
        category_records = [p for p in files if p.parent == category_dir]
        by_slug: dict[str, list[tuple[Path, dict]]] = {}
        for product_path in category_records:
            try:
                product_record = json.loads(product_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            product_obj = product_record.get("product") if isinstance(product_record, dict) else {}
            if not isinstance(product_obj, dict):
                continue
            product_slug = product_obj.get("model_slug") or product_obj.get("slug")
            if product_slug:
                by_slug.setdefault(str(product_slug), []).append((product_path, product_record))

        seen_scope_slugs: set[str] = set()
        for item in scope:
            if not isinstance(item, dict):
                warnings.append(f"{inventory_rel}: working_scope contains a non-object entry")
                continue
            inventory_records_checked += 1
            item_slug = str(item.get("slug") or item.get("model_slug") or "").strip()
            if not item_slug:
                warnings.append(f"{inventory_rel}: working_scope entry has no slug")
                continue
            if item_slug in seen_scope_slugs:
                warnings.append(f"{inventory_rel}: duplicate working_scope slug {item_slug!r}")
            seen_scope_slugs.add(item_slug)

            matches = by_slug.get(item_slug, [])
            if len(matches) != 1:
                warnings.append(
                    f"{inventory_rel}: inventory slug {item_slug!r} matches {len(matches)} product records "
                    f"in {category_dir.relative_to(ROOT).as_posix()}"
                )
                continue

            product_path, product_record = matches[0]
            source = product_record.get("source") if isinstance(product_record.get("source"), dict) else {}
            record_source_file = str(source.get("source_file") or "").strip()
            inventory_source_file = str(item.get("source_file") or "").strip()
            if inventory_source_file and not (ROOT / inventory_source_file).is_file():
                warnings.append(f"{inventory_rel}: archived source file missing for {item_slug!r}: {inventory_source_file!r}")
            if inventory_source_file and record_source_file and inventory_source_file != record_source_file:
                warnings.append(
                    f"{inventory_rel}: source_file mismatch for {item_slug!r}: "
                    f"inventory={inventory_source_file!r}, record={record_source_file!r}"
                )

            inventory_urls = {str(item.get(k) or "").strip() for k in ("url", "final_url")}
            inventory_urls.discard("")
            record_url = str(source.get("source_url") or "").strip()
            if inventory_urls and record_url and record_url not in inventory_urls:
                warnings.append(
                    f"{inventory_rel}: source_url mismatch for {item_slug!r}: "
                    f"record={record_url!r}, inventory={sorted(inventory_urls)!r}"
                )

            declared_sections = item.get("section_count")
            actual_sections = product_record.get("sections")
            if isinstance(declared_sections, int) and isinstance(actual_sections, list) and declared_sections != len(actual_sections):
                warnings.append(
                    f"{inventory_rel}: section_count mismatch for {item_slug!r}: "
                    f"inventory={declared_sections}, record={len(actual_sections)}"
                )

        unlisted = sorted(set(by_slug) - seen_scope_slugs)
        if unlisted:
            warnings.append(
                f"{inventory_rel}: {len(unlisted)} product records are not listed in working_scope: "
                + ", ".join(unlisted[:10])
            )
        if len(scope) != len(category_records):
            warnings.append(
                f"{inventory_rel}: working_scope has {len(scope)} entries but category contains "
                f"{len(category_records)} product records"
            )
        declared_count = (inventory.get("record_audit") or {}).get("product_record_count")
        if isinstance(declared_count, int) and declared_count != len(scope):
            warnings.append(
                f"{inventory_rel}: record_audit.product_record_count={declared_count} "
                f"but working_scope has {len(scope)} entries"
            )

    print(f"Inventories checked: {inventories_checked} | Inventory entries checked: {inventory_records_checked}")

    print(f"Product records scanned: {len(files)}")
    print(f"Records with no archived source file explicitly recorded: {source_archives_not_retained}")
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
