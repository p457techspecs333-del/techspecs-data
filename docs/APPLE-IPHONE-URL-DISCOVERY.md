# Apple iPhone URL discovery

The URL discovery script is intentionally separate from product-record extraction and validation.

## What it does

`scripts/discover_apple_iphone_urls.py` reads `data/catalogue.json`, selects records where brand is Apple, family is iPhone and category is smartphone, then searches for official Apple Ireland URLs. It checks candidate pages and writes a separate review file:

`sources/apple/iphone/url-discovery-candidates.json`

It does **not** modify product JSON records, source Markdown, or the catalogue.

A candidate marked `url_checked_model_name_found` means only that the URL returned HTTP 200, remained on an official Apple Ireland URL, and the model name was found in the retrieved page text. It is not a claim that every specification has been checked.

## One-time search setup

The first version uses Google's official Programmable Search JSON API rather than scraping Google result pages.

1. In Google Cloud Console, create or select a project.
2. Enable **Custom Search API** for that project.
3. Create an API key for the API.
4. Create a Programmable Search Engine at https://programmablesearchengine.google.com/.
5. Configure it to search the entire web, not just a short list of sites, and copy its Search Engine ID (CX).
6. Keep the API key private. Do not commit it to GitHub.

Set these environment variables in Windows PowerShell for the current terminal:

```powershell
$env:GOOGLE_CSE_API_KEY = "YOUR_API_KEY"
$env:GOOGLE_CSE_CX = "YOUR_SEARCH_ENGINE_ID"
```

## Install and run

From the repository root:

```powershell
python -m pip install -r requirements.txt
python scripts/discover_apple_iphone_urls.py --limit 5
```

Run one model:

```powershell
python scripts/discover_apple_iphone_urls.py --model "iPhone 17 Pro"
```

Run the full iPhone catalogue:

```powershell
python scripts/discover_apple_iphone_urls.py
```

The script uses a one-second delay between search requests by default. Google API quotas and billing limits apply.

## Review policy

- Apple Ireland pages are the only accepted candidate domains in this first pass.
- Search results from independent specification sites are deliberately excluded.
- Existing source URLs are retained in the output for comparison.
- Candidate URLs are never written into product records automatically.
- Review the output before any candidate is adopted as a product's primary source.
- A reachable URL is not the same as verified specification content.
