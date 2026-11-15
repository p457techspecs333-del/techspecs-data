# Samsung Galaxy S ingestion

This is a deliberately limited Samsung source stream for Apple-versus-Samsung phone comparisons. It is **not** a full Samsung catalogue.

## Included product scope

- One standard/base Galaxy S handset per generation (Galaxy S, S2–S10, S20–S26 where an official Samsung Ireland source page can be found).
- A generation is one product record, not one record per model number, finish, storage capacity, retailer SKU or carrier SKU.
- The discovery rule excludes Galaxy S+, S Plus, Ultra, FE, Edge and Active models.
- No Galaxy A, Z, tablets, watches, TVs or appliances are in scope.

The current standard model is Galaxy S26. Samsung's official Irish product page is:

- Product overview: https://www.samsung.com/ie/smartphones/galaxy-s26/
- Specifications: https://www.samsung.com/ie/smartphones/galaxy-s26/specs/

The page also describes the S26+ and Ultra family members. The ingestion workflow selects only the canonical base-model URL and does not create records for those variants.

## Workflow

From the repository root:

```bash
python -m pip install -r requirements.txt
python scripts/samsung_galaxy_s_ingest.py --discover
python scripts/samsung_galaxy_s_ingest.py --archive
python scripts/validate_product_records.py
python scripts/build_catalogue_index.py
```

- `--discover` creates `data/samsung/smartphones/source-inventory.json`.
- `--archive` fetches candidate official Samsung Ireland pages, saves original HTML under `sources/samsung/galaxy-s/`, and creates V2 records under `data/samsung/smartphones/`.
- Historical URL candidates are not assumed to exist. A missing, blocked or unreadable page is reported in the inventory and is not represented as a verified product record.
- Generated records start at `url_checked` and `archival_first_pass`. The script does not claim field-level specification verification.

## Comparison with Apple

Samsung and Apple records share the canonical TechSpecs V2 schema. The Apple product records remain unchanged. The catalogue generator indexes both manufacturer folders using their full repository-relative paths, so the resulting product URLs remain unique.

Do not infer a one-to-one generation match from release year alone. The human-facing comparison layer should compare products using the same normalized field vocabulary and display missing or non-comparable fields explicitly.
