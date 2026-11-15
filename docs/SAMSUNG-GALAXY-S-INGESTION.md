# Samsung ingestion — slim comparison scope

This workstream builds a **small Samsung comparison catalogue**, not a complete Samsung catalogue.

## Agreed scope

1. **Phones:** identify Samsung equivalents for the complete legacy/current iPhone catalogue. Samsung model families and variants must be selected by genuine product equivalence, not by release year alone. A Galaxy S base model is not automatically an equivalent for every iPhone Pro, Pro Max, mini or Plus model. Keep one record per actual product model; colour and storage SKUs are attributes, not separate products.
2. **Other categories:** include only the latest current Samsung products with a genuine counterpart in the current Apple catalogue. Do not create historical Samsung back-catalogues for tablets, laptops, watches, earbuds, displays or other categories.
3. **No forced matches:** where Samsung has no credible equivalent, record the gap in the comparison mapping rather than inventing a product.

The current Apple catalogue contains 50 iPhone records. That is the phone-matching workload; it is not a promise that there will be exactly 50 Samsung records because some Apple models may share a closest Samsung equivalent and some may have no direct counterpart.

## Source collection and extraction

Samsung's live pages can freeze a normal browser. The scraper therefore downloads the source HTML directly with a low request rate and parses the server-rendered product specification component without launching a browser.

The Samsung product detail template currently exposes specification data in:

- `.pdd32-product-spec`
- `.pdd32-product-spec__item`
- `.pdd32-product-spec__content-item-title`
- `.pdd32-product-spec__content-item-desc`

The scraper preserves each specification heading and label/value pair as a V2 `sections` entry, and writes corresponding `normalized_specifications` values with `verification_status: source_transcribed`. This means the value was transcribed from Samsung's HTML; it is not yet independently field-verified. The original HTML is retained as source evidence.

A page returning HTTP 200 is not sufficient to create a record. The scraper must also check the requested product identity and confirm that the specification component exists before treating the page as a successful specification extraction.

## Current implementation boundary

The existing `samsung_galaxy_s_ingest.py` is the first phone-family adapter. It currently discovers canonical standard Galaxy S generations only; it does **not yet** complete the full cross-family iPhone equivalence mapping or the current-only non-phone categories. Do not treat its current output as the finished slim Samsung catalogue.

The next implementation step is to expand discovery to the Samsung phone families needed for real iPhone equivalents, then add a current-model-only pass for the other Apple-matched categories. The original Apple records remain unchanged.

## Commands

From the repository root:

```bash
python -m pip install -r requirements.txt
python scripts/samsung_galaxy_s_ingest.py --discover
python scripts/samsung_galaxy_s_ingest.py --archive
python scripts/validate_product_records.py
python scripts/build_catalogue_index.py
```

New records must validate against `schemas/product-record-v2.schema.json`. Do not mark fields `content_verified` merely because they were extracted from the source HTML.
