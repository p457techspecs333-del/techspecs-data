# TechSpecs consumer website

This folder contains the first human-facing TechSpecs website experience. It is intentionally separate from the machine-facing data interface in `data.techspecs.dev`.

## Current implementation

- Responsive Ireland-first homepage for `techspecs.ie`.
- Product discovery powered by the published catalogue at `https://data.techspecs.dev/catalogue.json`.
- Search across brand, model, family and category.
- Category filters and product detail views.
- Side-by-side comparison of fields actually present in the selected V2 product records.
- Direct links to original manufacturer sources and the machine-readable record interface.
- No invented prices, ratings, recommendations or unsupported specifications.

## Deploy as a separate Cloudflare Pages project

Create a new Pages project connected to this GitHub repository, using:

- Production branch: `main`
- Root directory: `website`
- Build command: none
- Build output directory: `.`

Attach `techspecs.ie` and `www.techspecs.ie` to this Pages project after DNS is configured. Keep the existing `data.techspecs.dev` project and its deployment settings unchanged.

## Required data-host configuration

The browser frontend requests the catalogue and individual JSON records from `data.techspecs.dev`. The data host must return an appropriate CORS header allowing the production website origin:

```
Access-Control-Allow-Origin: https://techspecs.ie
```

Also allow `https://www.techspecs.ie` if the www hostname is used. Until this is configured, browsers may block catalogue loading even when the JSON endpoints themselves are publicly accessible.

## Important data behaviour

The V2 records are archival-first and normalized fields are not uniformly complete. The comparison view therefore only displays fields actually present in the selected records and labels missing values as unavailable. It does not infer or fabricate missing values.

The initial catalogue is Apple-heavy. The category landing page advertises the broader TechSpecs ambition, but categories and manufacturers should only become fully searchable when their records are present in the published catalogue.
