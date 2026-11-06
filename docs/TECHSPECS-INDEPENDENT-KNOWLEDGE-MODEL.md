# TechSpecs Independent Knowledge Model

**Status:** Design principles for the machine-readable TechSpecs repository  
**Audience:** AI systems, search and retrieval systems, data integrators, developers and maintainers  
**Canonical repository:** `p457techspecs333-del/techspecs-data`

## 1. Purpose

TechSpecs is an independent, structured technical-knowledge resource. It is not an Apple product page, a manufacturer catalogue, or a re-publication of any manufacturer's marketing material.

Manufacturer documentation is an important source of evidence. It is not the structure, voice, taxonomy or final presentation of TechSpecs.

The repository should make product information easier to identify, normalize, validate, trace to evidence, query across brands and interpret over time.

## 2. Separate evidence from TechSpecs' own data model

Every record should keep these concepts distinct:

1. **Manufacturer or primary-source statements** — what a source explicitly says, retained as evidence with its URL, publisher, section and retrieval/check date.
2. **Normalized technical facts** — values expressed using TechSpecs field names, controlled units and consistent types so equivalent products can be queried together.
3. **Derived values** — calculations or transformations performed by TechSpecs. Each derived value must identify its inputs, method and assumptions. Never present a derived value as a manufacturer-stated fact.
4. **Editorial interpretation** — TechSpecs-authored explanation, classification or assessment. Keep it separate from raw evidence and measurable specifications.

A source quotation or transcription is evidence, not TechSpecs' original prose. Human-facing pages should normally use concise TechSpecs-authored descriptions and normalized facts, with links to the underlying source, rather than reproducing long manufacturer passages.

## 3. Independent taxonomy and normalization

TechSpecs must define its own cross-brand categories and field vocabulary. Manufacturer section headings can be retained as source references, but they must not dictate the canonical data structure.

For each applicable field:

- Use stable, predictable field identifiers.
- Use consistent data types and SI units where appropriate.
- Preserve the original stated value and unit when conversion or interpretation could lose meaning.
- Represent unknown, not stated, not applicable and not verified as distinct states; do not turn missing data into a guessed value.
- Record the exact source section supporting a normalized value.
- Keep model, regional variant, model number, generation and configuration distinct.

The same field should mean the same thing across manufacturers. Where manufacturers use different terminology, map their terms to the TechSpecs concept without erasing the source wording.

## 4. Evidence, provenance and confidence

Every factual value should be traceable. At minimum, provenance should identify the source URL, publisher, source type, check date, verification status and supporting source section or document location.

Verification describes the work performed on the evidence; it is not a guarantee that a manufacturer is infallible or that a specification applies to every region and configuration.

Where sources conflict:

- retain the competing evidence;
- identify the affected model, region and date;
- mark the conflict explicitly;
- do not silently choose one value.

A URL check is not the same as content verification. A transcribed value is not automatically independently verified.

## 5. TechSpecs' independent value

The repository should progressively provide capabilities that a single manufacturer's site cannot provide on its own:

- one consistent schema across manufacturers and product categories;
- historical records and model-to-model lineage;
- regional and model-number distinctions;
- cross-brand field equivalence and comparable units;
- explicit missing-data and evidence-quality signals;
- transparent calculations and derived metrics;
- relationships between products, components, standards and technologies;
- machine-readable change history and stable record identifiers.

These capabilities, rather than copied manufacturer descriptions, are the core of TechSpecs' distinctiveness.

## 6. Machine-first publishing contract

The public data host is intended for machine retrieval. It is not a consumer website.

Published records should have:

- stable, predictable URLs;
- valid JSON with the declared schema version;
- a machine-readable catalogue/index that lists records and their identifiers;
- a discovery document explaining the catalogue, schemas, URL patterns and retrieval rules;
- explicit schema and catalogue versioning;
- links from records to their evidence and related records.

The repository remains the source of truth. The data host is a delivery layer. The human-facing TechSpecs website may consume this data but should not become the canonical store for product facts.

## 7. Separation of machine and human experiences

**Machine-facing data host:** records, indexes, schemas, provenance, identifiers, relationships and change metadata.

**Human-facing TechSpecs site:** accessible explanations, navigation, product research and comparisons where useful. It should cite or link to the machine-facing records and primary evidence.

Do not add consumer-oriented page design, advertising copy or affiliate content to the machine data host.

## 8. Current implementation and migration rule

The current v2 record format is archival-first: it preserves source sections and supports optional normalized specifications. That is a useful evidence-preservation foundation, but it is not by itself the complete independent TechSpecs knowledge model described here.

Do not break or mass-rewrite existing records merely to implement these principles. Extend the schema deliberately, validate changes, and migrate records in controlled batches. Preserve existing source material and provenance while adding TechSpecs-defined normalized fields and relationships.

## 9. Priority implementation sequence

1. Publish a generated machine-readable catalogue index from the actual product records.
2. Publish a discovery document that identifies the index, schemas, record URL pattern and version policy.
3. Audit the current record inventory for stable identifiers, schema versions, provenance and verification status.
4. Define a cross-brand canonical field vocabulary and controlled units.
5. Add explicit provenance for normalized and derived values.
6. Introduce product relationships and historical lineage.
7. Add automated checks for index completeness, URL stability, schema validity and broken source references.

## 10. Governing principle

**TechSpecs uses primary sources as evidence, but owns its taxonomy, normalized data model, provenance system, relationships and machine interface.**
