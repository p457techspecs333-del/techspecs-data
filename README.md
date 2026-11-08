# TechSpecs Data

Independent, machine-readable technical knowledge and historical product records for TechSpecs.

TechSpecs uses manufacturer and other primary sources as evidence. It defines its own record identifiers, taxonomy, normalized data model, provenance conventions and discovery interface. This repository is not intended to be a consumer-facing website.

## Start here

- **Machine catalogue:** https://data.techspecs.dev/catalogue.json
- **Machine discovery instructions:** https://data.techspecs.dev/llms.txt
- **Published product records:** https://data.techspecs.dev/
- **Canonical product schema:** [schemas/product-record-v2.schema.json](schemas/product-record-v2.schema.json)
- **Independent knowledge model:** [docs/TECHSPECS-INDEPENDENT-KNOWLEDGE-MODEL.md](docs/TECHSPECS-INDEPENDENT-KNOWLEDGE-MODEL.md)

## How to discover records

Use the catalogue as the authoritative list of published records. Each entry provides a stable repository-relative `record_id`, record path, public URL, product identifiers and source/verification metadata.

Do not guess a record URL and assume the record exists. Retrieve the catalogue first, then fetch the URL listed for the required record.

Example record:
`https://data.techspecs.dev/apple/iphone/iphone-17.json`

## Interpreting records

- Manufacturer statements and retained source transcriptions are evidence, not TechSpecs-authored conclusions.
- Normalized values must be interpreted with their units, source-section references and verification status.
- Derived values must be labelled and document their inputs and method.
- Missing, unknown, not applicable and unverified are not interchangeable.
- A source URL being reachable does not by itself mean its content has been verified.

## Repository layout

- `data/` — product records and generated machine catalogue; published by Cloudflare Pages.
- `sources/` — archived source material used to preserve provenance.
- `schemas/` — canonical record schemas.
- `scripts/` — validation and catalogue-generation tools.
- `docs/` — data-model and migration documentation.
- `.github/workflows/` — automated record validation and catalogue generation.

## Validation and catalogue generation

Install dependencies and run:

```bash
python -m pip install -r requirements.txt
python scripts/validate_product_records.py
python scripts/build_catalogue_index.py
```

The GitHub Actions workflow validates product records and regenerates `data/catalogue.json` when relevant files change. The catalogue is a discovery index, not a substitute for reading and validating individual records.

## Apple iPhone URL discovery

The non-destructive URL discovery workflow is documented in [docs/APPLE-IPHONE-URL-DISCOVERY.md](docs/APPLE-IPHONE-URL-DISCOVERY.md). It searches for official Apple Ireland product URLs and writes candidates to a separate review file; it does not modify product records.

## Canonical source

The GitHub repository is the source of truth. `data.techspecs.dev` is the public machine-retrieval layer; the human-facing TechSpecs site is a separate experience.
