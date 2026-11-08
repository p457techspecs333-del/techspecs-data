# Apple iPhone URL discovery

The URL discovery script is intentionally separate from product-record extraction and validation.

## What it does

`scripts/discover_apple_iphone_urls.py` reads `data/catalogue.json`, selects records where brand is Apple, family is iPhone and category is smartphone, then searches for official Apple Ireland URLs using the Brave Search API. It checks candidate pages and writes a separate review file:

`sources/apple/iphone/url-discovery-candidates.json`

It does **not** modify product JSON records, source Markdown, or the catalogue.

A candidate marked `url_checked_model_name_found` means only that the URL returned HTTP 200, remained on an official Apple Ireland URL, and the model name was found in the retrieved page text. It is not a claim that every specification has been checked.

## One-time search setup

The script uses the Brave Search API. Create an account, choose an API plan, and create an API key at:

https://api.search.brave.com/app/keys

Check the current plan, pricing and usage limits in the Brave dashboard before activating it. Keep the API key private. Do not commit it to GitHub or paste it into chat.

In Windows PowerShell, set the key for the current terminal session:

```powershell
$env:BRAVE_API_KEY = "YOUR_BRAVE_API_KEY"
```

The script reads the key from that environment variable. It does not print or save the key.

## Install and run

From the repository root in PowerShell:

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

The script uses a one-second delay between search requests by default. Brave API plan limits and usage charges apply.

## Review policy

- Apple Ireland pages are the only accepted candidate domains in this first pass.
- Search results from independent specification sites are deliberately excluded.
- Existing source URLs are retained in the output for comparison.
- Candidate URLs are never written into product records automatically.
- Review the output before any candidate is adopted as a product's primary source.
- A reachable URL is not the same as verified specification content.
