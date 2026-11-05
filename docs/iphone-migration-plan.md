# iPhone catalogue migration plan

**Status:** Planning document  
**Scope:** Existing iPhone source archive and JSON records  
**Principle:** Preserve supplied source material; improve structure and verification without inventing or silently changing specifications.

## Starting position

The inventory audit found:

- 48 iPhone JSON records and 48 matching model source Markdown files.
- All 48 JSON files parsed successfully at the time of the audit.
- The records are not yet certified as compliant with product-record schema v2.
- Three broad record shapes are present: section-preserving records using `extraction`, section-preserving records using `extraction_note`, and a legacy field-level record.
- Source URL and verification metadata are incomplete in a number of records.
- The standard iPhone 6 is absent while iPhone 6 Plus is present. Do not create a standard iPhone 6 record without an attributable source and clear model-specific evidence.

See [the catalogue audit](../reports/iphone-catalogue-audit.md) for the inventory and detailed findings.

## Migration rules

1. Keep every original `*-source.md` file unchanged.
2. Never infer a specification from a sibling model, product family, retailer listing, or general knowledge.
3. Keep unknown values unknown. Do not convert missing data into zero, false, or "not applicable".
4. Record provenance and verification at field level when normalized specifications are added.
5. Use `source_url: null` when a canonical source URL has not been checked. Do not promote an embedded or guessed URL to a verified source.
6. Keep archival source text separate from normalized fields.
7. Migrate in small batches and run the automated validator after each batch.
8. Treat schema validity as structural quality, not proof of factual accuracy.

## Recommended phases

### Phase 1 — Prepare the record inventory

- Produce a per-record migration register with current shape, source pairing, provenance gaps, and proposed review status.
- Identify records with explicit manufacturer source material versus user-supplied or third-party material.
- Do not change product JSON during this phase.

### Phase 2 — Pilot the v2 representation

- Select one record with a clear, attributable source and enough information to test normalized fields.
- Preserve all source sections verbatim.
- Add only a small, useful set of normalized fields first: identity, display, dimensions, weight, battery, charging, connectivity, and launch information where supported.
- Link each normalized value to its source section and give it an honest verification status.
- Validate the pilot against `schemas/product-record-v2.schema.json`.
- Review the result before applying the approach to other records.

### Phase 3 — Migrate in controlled batches

- Migrate a small number of closely related models at a time.
- Keep model-specific differences explicit; do not copy values between models unless the source explicitly supports that.
- After each batch, run GitHub Actions and inspect warnings and failures.
- Update the migration register so progress and outstanding evidence gaps remain visible.

### Phase 4 — Verify facts and provenance

- Check manufacturer claims against attributable primary sources wherever possible.
- Record the date checked and the exact source used.
- Where primary sources are unavailable, retain the record as unverified or partially verified rather than implying certainty.
- Resolve conflicts by recording the conflicting evidence and rationale; do not silently choose a value.

### Phase 5 — Expand beyond phones

- Reuse the same schema and validation principles for other product categories.
- Add category-specific normalized field groups only when there is a clear comparison use case.
- Avoid forcing unrelated product types into phone-specific fields.

## Completion criteria

A record is ready for use in structured comparisons only when:

- Its product identity and variant are unambiguous.
- Its normalized fields validate against schema v2.
- Each displayed comparison value has traceable source provenance.
- Unknown, unavailable, and not-applicable values are distinguished.
- Material conflicts and verification limitations are visible.
- The source archive remains preserved.

A successful automated run is necessary for structural quality, but is not sufficient for factual certification.
