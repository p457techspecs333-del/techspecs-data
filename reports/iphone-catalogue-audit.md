# iPhone Catalogue — Repository Inventory and Data Audit

**Audit date:** 5 November 2026  
**Repository:** `p457techspecs333-del/techspecs-data`  
**Branch:** `main`  
**Audited tree SHA:** `5081a264c9fa97a79c26a3f4c88de5a3f5477a2c`  
**Scope:** Complete Git tree inventory; all JSON files under `data/apple/iphone/`; corresponding Markdown files under `sources/apple/iphone/`.

## Executive summary

- **48** iPhone JSON records found.
- **48** model source Markdown files found.
- **48/48 JSON files parsed successfully** (no JSON syntax failures encountered).
- **48/48 JSON records have a matching source Markdown file reference/name** based on model slug.
- **One catalogue gap:** standard iPhone 6 has no JSON record and no source Markdown file. iPhone 6 Plus exists and is a separate model.
- **Schema inconsistency:** records use three materially different top-level shapes. The iPhone 6 Plus record is a legacy field-level extraction; most others are section-preserving archives.
- **Provenance is incomplete:** nearly all records have no populated source URL. One record (iPhone 17e) contains an Apple URL but explicitly says it was inferred and not independently checked.
- **The newer supplied iPhone 17e, iPhone 18 Pro/Pro Max and iPhone Duo records are not independently verified.** Their presence in the repository is not evidence that the supplied specifications are official or accurate.

This audit establishes repository structure, JSON syntax validity, and basic source pairing. It does **not** establish factual correctness of product specifications, exhaustive field completeness, or current Apple support status.

## 1. Repository coverage

### Model records present

| Model group | JSON records |
|---|---|
| iPhone 5 generation | iPhone 5, 5c, 5s |
| iPhone 6 generation | iPhone 6 Plus, 6s, 6s Plus |
| iPhone 7 generation | iPhone 7, 7 Plus |
| iPhone 8 generation | iPhone 8, 8 Plus |
| iPhone X generation | iPhone X |
| iPhone XR generation | iPhone XR |
| iPhone XS generation | iPhone XS, XS Max |
| iPhone 11 generation | iPhone 11, 11 Pro, 11 Pro Max |
| iPhone 12 generation | iPhone 12, 12 mini, 12 Pro, 12 Pro Max |
| iPhone 13 generation | iPhone 13, 13 mini, 13 Pro, 13 Pro Max |
| iPhone 14 generation | iPhone 14, 14 Plus, 14 Pro, 14 Pro Max |
| iPhone 15 generation | iPhone 15, 15 Plus, 15 Pro, 15 Pro Max |
| iPhone 16 generation | iPhone 16, 16 Plus, 16 Pro, 16 Pro Max |
| iPhone 17 generation | iPhone 17, 17e, 17 Pro, 17 Pro Max |
| iPhone 18 generation | iPhone 18 Pro, 18 Pro Max, iPhone Duo |
| iPhone Air | iPhone Air |
| iPhone SE | iPhone SE (1st, 2nd and 3rd generations) |

### Identified catalogue gap

- **iPhone 6 (standard):** absent from both `data/apple/iphone/` and the source Markdown collection.
- **iPhone 6 Plus:** present, but its own source metadata explicitly warns that some sections cover iPhone 6 and iPhone 6 Plus together and must be checked for model applicability before any future standard iPhone 6 record is created.

No other missing model is asserted by this audit. The inventory describes what is in this repository, not every iPhone Apple has ever released.

## 2. Source-to-record pairing

- 48 JSON records.
- 48 model-specific source Markdown files.
- All 48 model slugs have a corresponding Markdown filename ending in `-source.md`.
- The only additional Markdown file is `sources/apple/iphone/README.md`, which is a directory-level readme rather than a model source.
- No orphan model JSON or orphan model Markdown file was found by filename-stem comparison.

Pairing is based on repository paths and model filename stems. It does not prove that every JSON section is a complete or lossless transcription of its Markdown source.

## 3. JSON syntax and schema findings

### Syntax validation

All 48 JSON files were fetched from the default branch and parsed as JSON. No syntax errors were found.

### Top-level structure variants

The inventory contains three main structural patterns:

1. **Section-preserving archival records** — `schema_version`, `product`, `source`, `extraction`, `sections`. This is the dominant pattern.
2. **Section-preserving records with `extraction_note` instead of `extraction`** — found in some newer supplied records, including iPhone 17e, iPhone 18 Pro, iPhone 18 Pro Max and iPhone Duo.
3. **Legacy field-level extraction** — iPhone 6 Plus uses `schema_version`, `product`, `specifications`, `source`, with no `sections` array.

The product metadata also varies: examples include `name` versus `model`, `model_slug`, `year_introduced` versus `model_year`, and different source verification field names. These variations complicate reliable programmatic comparison and quality checks.

### Interpretation

Most records are archival first passes that preserve source text by section. They are not yet fully normalized field-by-field specifications. The iPhone 6 Plus record is different: it contains a partial structured `specifications` object, and its own source notes say to consult the Markdown for details omitted from that extraction.

A successful JSON parse only confirms valid syntax. It does not confirm that values are correct, complete, comparable, or sourced from Apple.

## 4. Provenance and verification

The source metadata is not yet consistent enough to support a simple repository-wide verified/unverified status.

Observed examples include:
- `source_url: null` with a separate `verification_status` or `source_status`.
- A populated Apple URL in the iPhone 17e record, while its metadata says the URL was inferred from page links and not independently checked.
- Different source type labels such as `user_supplied_document`, `User-supplied source document`, and `user_supplied_markdown`.
- Both `verification_status` and `verification` used for related concepts.

**Audit conclusion:** treat the current collection as user-supplied source material unless a source URL has been independently checked and the individual specification values have been verified. Do not label the catalogue Apple-verified based on the current metadata.

## 5. Quality risks and priorities

| Priority | Finding | Why it matters |
|---|---|---|
| High | Inconsistent JSON schemas | Applications cannot safely assume the same fields or data types across all models. |
| High | Incomplete provenance | Users and downstream systems cannot reliably trace claims to an authoritative source. |
| High | Archival text is not normalized | Direct product comparisons and filters cannot yet depend on consistent field values. |
| High | Newer supplied records are unverified | Their content should not be presented as confirmed manufacturer specifications. |
| Medium | iPhone 6 standard is absent | Coverage is incomplete for the iPhone 6 generation. |
| Medium | iPhone 6 Plus extraction is partial | Its structured fields alone do not represent all information in the source Markdown. |
| Medium | Product/source metadata naming varies | Makes validation, indexing and maintenance harder. |

## 6. Recommended remediation sequence

1. **Freeze and preserve the source archive.** Keep every supplied Markdown source unchanged; do not discard or overwrite it during normalization.
2. **Define a canonical JSON schema.** Agree required product identity fields, model identifiers, source metadata, verification states, normalized specification groups, units, and explicit unknown/not-applicable handling.
3. **Create validation rules.** Validate required fields, allowed types, units, duplicate model identifiers, source references, and model-specific applicability.
4. **Normalize in controlled batches.** Convert from source Markdown into canonical fields while retaining original section text and recording the mapping. Do not infer missing values.
5. **Verify authoritative sources.** For each model, locate and check the correct Apple specification source (or a clearly documented alternative for unavailable historical pages). Record exact URL, retrieval/check date, and verification scope.
6. **Resolve the iPhone 6 gap** only from a separate, attributable source document. Do not derive its record by copying shared iPhone 6 Plus sections without checking applicability.
7. **Add comparison-readiness checks.** Compare common fields across models only after units, definitions, and missing-value semantics are consistent.

## 7. Audit limitations

- This audit checked the complete Git tree and parsed all 48 JSON files, but it did not fact-check every specification against Apple's pages.
- It did not compare every Markdown character against its JSON section text or verify that every footnote, table, and embedded link was preserved.
- It did not assess image rights, licensing, update cadence, redirects, or current availability of historical Apple pages.
- Model coverage is repository coverage only; it is not a claim of exhaustive coverage of the global iPhone catalogue.

## 8. Full JSON inventory

```text
data/apple/iphone/
iphone-11.json
iphone-11-pro.json
iphone-11-pro-max.json
iphone-12.json
iphone-12-mini.json
iphone-12-pro.json
iphone-12-pro-max.json
iphone-13.json
iphone-13-mini.json
iphone-13-pro.json
iphone-13-pro-max.json
iphone-14.json
iphone-14-plus.json
iphone-14-pro.json
iphone-14-pro-max.json
iphone-15.json
iphone-15-plus.json
iphone-15-pro.json
iphone-15-pro-max.json
iphone-16.json
iphone-16-plus.json
iphone-16-pro.json
iphone-16-pro-max.json
iphone-17.json
iphone-17e.json
iphone-17-pro.json
iphone-17-pro-max.json
iphone-18-pro.json
iphone-18-pro-max.json
iphone-5.json
iphone-5c.json
iphone-5s.json
iphone-6-plus.json
iphone-6s.json
iphone-6s-plus.json
iphone-7.json
iphone-7-plus.json
iphone-8.json
iphone-8-plus.json
iphone-air.json
iphone-duo.json
iphone-se-1st-generation.json
iphone-se-2nd-generation.json
iphone-se-3rd-generation.json
iphone-x.json
iphone-xr.json
iphone-xs.json
iphone-xs-max.json
```

---
**Status:** Inventory and syntax audit complete. Canonical schema design and factual source verification remain outstanding.

## Addendum — 6 November 2026 source URL intake

This addendum supersedes the provenance findings above where they describe source URLs as absent; the original inventory and schema findings remain a 5 November snapshot.

- The project owner supplied **47 Apple Support URLs**. The intake register is `reports/apple-iphone-source-url-intake-2026-11-06.md`.
- **19 existing JSON records were updated** to use the supplied Ireland URLs where the existing URL was missing, used another locale, pointed to the wrong variant, or was a product page instead of the supplied Support page.
- The other supplied URLs that already matched existing records were retained as assigned.
- Three 1485xx URLs appear to correspond to iPhone 18 Pro, iPhone 18 Pro Max and iPhone Duo, but direct page retrieval did not complete during this check; their final URL verification remains pending.
- Two supplied pages point to models missing from the repository: **standard iPhone 6** (the existing iPhone 6 Plus record is not a substitute) and **iPhone 16e**. Their URLs are preserved in the intake register; records and source Markdown still need to be created from attributable source material.
- URL assignment is not specification verification. Field-by-field comparison, normalized-field review, and a fresh catalogue-wide provenance audit remain outstanding.

The most recent JSON-source update triggered GitHub Actions validation successfully. See [the workflow run](https://github.com/p457techspecs333-del/techspecs-data/actions/runs/42202854143).

