# iPhone record migration register

**Inventory reviewed:** 5 November 2026  
**Scope:** 48 JSON records under `data/apple/iphone/`  
**Purpose:** Track migration readiness without modifying original product records or source Markdown.

## Overall assessment

- **48 records** inventoried; all 48 had matching source Markdown in the repository inventory audit.
- **43** use the common section-preserving shape with an `extraction` object.
- **4** use the section-preserving shape with `extraction_note` instead (`iphone-17e`, `iphone-18-pro`, `iphone-18-pro-max`, `iphone-duo`).
- **1** uses the older field-level `specifications` shape (`iphone-6-plus`).
- **8** records have been migrated to schema v2 with pilot normalized fields; the other 40 records remain unmigrated.
- The iPhone 16 and iPhone 17 pilots have official Apple Support Ireland source pages checked on 5 November 2026; the iPhone 17 Pro and iPhone 17 Pro Max pilots use Apple's Ireland product specifications page, checked on the same date. The iPhone 17e record still has an inferred URL that has not been independently checked.
- Several records have blank verification status metadata. Other records explicitly say they were transcribed from supplied documents and the source page URL was not independently verified.

**Meaning:** The archive is useful source material, but it is not yet a field-normalized, independently verified comparison database. A passing structural validator does not change that assessment.

## Record-by-record register

| Slug | Product | Year | Sections | Current shape | Provenance position | Next action |
|---|---|---:|---:|---|---|---|
| `iphone-5` | iPhone 5 | 2012 | 21 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-5c` | iPhone 5c | 2013 | 30 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-5s` | iPhone 5s | 2013 | 30 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-6-plus` | iPhone 6 Plus | — | — | Legacy field-level | URL absent; not independently verified; applicability caveat in source | Special review |
| `iphone-6s` | iPhone 6s | 2015 | 33 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-6s-plus` | iPhone 6s Plus | 2015 | 33 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-7` | iPhone 7 | 2016 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-7-plus` | iPhone 7 Plus | 2016 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-8` | iPhone 8 | 2017 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-8-plus` | iPhone 8 Plus | 2017 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-x` | iPhone X | 2017 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-xr` | iPhone XR | 2018 | 33 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-xs` | iPhone XS | 2018 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-xs-max` | iPhone XS Max | 2018 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-11` | iPhone 11 | 2019 | 33 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-11-pro` | iPhone 11 Pro | 2019 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-11-pro-max` | iPhone 11 Pro Max | 2019 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-se-1st-generation` | iPhone SE (1st generation) | 2016 | 33 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-se-2nd-generation` | iPhone SE (2nd generation) | 2020 | 33 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-se-3rd-generation` | iPhone SE (3rd generation) | 2022 | 32 | Section archive | Embedded URLs preserved; canonical page unverified | Provenance review |
| `iphone-12` | iPhone 12 | 2020 | 36 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-12-mini` | iPhone 12 mini | 2020 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-12-pro` | iPhone 12 Pro | 2020 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-12-pro-max` | iPhone 12 Pro Max | 2020 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-13` | iPhone 13 | 2021 | 33 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-13-mini` | iPhone 13 mini | 2021 | 38 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-13-pro` | iPhone 13 Pro | 2021 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-13-pro-max` | iPhone 13 Pro Max | 2021 | 34 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-14` | iPhone 14 | 2022 | 35 | Section archive | URL absent; verification status blank | Provenance review |
| `iphone-14-plus` | iPhone 14 Plus | 2022 | 35 | Section archive | URL absent; verification status blank | Provenance review |
| `iphone-14-pro` | iPhone 14 Pro | 2022 | 35 | Section archive | URLs within document preserved; canonical page unverified | Provenance review |
| `iphone-14-pro-max` | iPhone 14 Pro Max | 2022 | 35 | Section archive | URLs within document preserved; canonical page unverified | Provenance review |
| `iphone-15` | iPhone 15 | 2023 | 36 | Section archive | URL absent; verification status blank | Provenance review |
| `iphone-15-plus` | iPhone 15 Plus | 2023 | 35 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-15-pro` | iPhone 15 Pro | 2023 | 36 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-15-pro-max` | iPhone 15 Pro Max | 2023 | 36 | Section archive | URL absent; supplied document | Provenance review |
| `iphone-16` | iPhone 16 | 2024 | 37 | **v2 pilot migrated** | Official Apple Support Ireland page checked 2026-11-05; original sections preserved | Pilot fields normalized; continue field-by-field review |
| `iphone-16-plus` | iPhone 16 Plus | 2024 | 37 | **v2 pilot migrated** | Apple Support specifications page checked 2026-11-05; original sections preserved | Pilot fields normalized; continue field-by-field review |
| `iphone-16-pro` | iPhone 16 Pro | 2024 | 37 | **v2 pilot migrated** | Apple Support specifications page checked 2026-11-05; original sections preserved | Pilot fields normalized; continue field-by-field review |
| `iphone-16-pro-max` | iPhone 16 Pro Max | 2024 | 37 | **v2 pilot migrated** | Apple Support Ireland specifications page checked 2026-11-05; original sections preserved | Pilot fields normalized; continue field-by-field review |
| `iphone-air` | iPhone Air | 2025 | 36 | **v2 pilot migrated** | Official Apple Ireland specifications page checked 2026-11-05; original sections preserved | Pilot fields normalized; continue field-by-field review |
| `iphone-17` | iPhone 17 | 2025 | 30 | **v2 pilot migrated** | Official Apple Support Ireland page checked 2026-11-05; original sections preserved | Pilot fields normalized; continue field-by-field review |
| `iphone-17-pro` | iPhone 17 Pro | 2025 | 37 | **v2 pilot migrated** | Official Apple Ireland specifications page checked 2026-11-05; original sections preserved | Pilot fields normalized; continue field-by-field review |
| `iphone-17-pro-max` | iPhone 17 Pro Max | 2025 | 37 | **v2 pilot migrated** | Official Apple Ireland specifications page checked 2026-11-05; original sections preserved | Pilot fields normalized; continue field-by-field review |
| `iphone-17e` | iPhone 17e | 2026 | 37 | Section archive | Apple UK URL inferred; not independently checked | Verify URL first |
| `iphone-18-pro` | iPhone 18 Pro | 2026 | 37 | Section archive (extraction_note) | URL absent; verification status blank | Source/claim review before normalization |
| `iphone-18-pro-max` | iPhone 18 Pro Max | 2026 | 37 | Section archive (extraction_note) | URL absent; verification status blank | Source/claim review before normalization |
| `iphone-duo` | iPhone Duo | 2026 | 37 | Section archive (extraction_note) | URL absent; supplied document | Source/claim review before normalization |

## Migration priority and handling

### Priority 1 — Resolve source evidence before normalizing

- **iPhone 17e:** verify the inferred Apple UK URL and confirm that it resolves to the intended product specification page before treating it as a canonical source.
- **iPhone 18 Pro, iPhone 18 Pro Max and iPhone Duo:** source metadata and verification status are incomplete. Establish what the supplied source documents represent and whether claims can be attributed to reliable primary evidence before using them as verified product facts.
- **iPhone 6 Plus:** retain its legacy shape for now. Its existing extraction is partial, and the source notes warn that some material may apply to both iPhone 6 and iPhone 6 Plus. Do not use it as the basis for a standard iPhone 6 record.

### Priority 2 — Choose a conservative pilot

Choose one record only after its source document and product identity are clear. The pilot should:
1. Preserve its source Markdown unchanged.
2. Add schema v2 metadata.
3. Normalize only a small group of clearly attributable fields.
4. Attach a source section and verification status to each normalized field.
5. Pass the v2 schema and receive a human evidence review before the pattern is repeated.

The register does not nominate a record as factually verified. That would require checking its source evidence, not just inspecting its JSON structure.

### Priority 3 — Batch migration

After the pilot is approved, migrate in small groups. Keep the register current, run GitHub Actions after each batch, and leave unresolved values unknown. Do not copy specifications between model variants without explicit source support.

## Important catalogue gap

The standard **iPhone 6** record is absent from the current inventory, while iPhone 6 Plus exists. This is a catalogue gap to investigate, not permission to create a record from the Plus model or from family-level source text.

## Status definitions

- **Provenance review:** establish and record a canonical source and honest verification status before relying on normalized values.
- **Verify URL first:** the stored URL is inferred and needs direct checking.
- **Source/claim review before normalization:** establish the source basis and review claims before converting them into normalized facts.
- **Special review:** retain the legacy record until its applicability and partial extraction are understood.

## Change control

This register tracks migration progress; it does not alter source Markdown. The iPhone 16 JSON record was migrated to schema v2 as a pilot on 5 November 2026, and its 37 preserved sections remain intact. Only its listed normalized pilot fields were checked against the official Apple page. Update a row only when a source check, migration, or review has actually been completed. Never label a record verified solely because it passes JSON Schema validation.
