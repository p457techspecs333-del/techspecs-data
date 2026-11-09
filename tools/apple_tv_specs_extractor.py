#!/usr/bin/env python3
"""Extract Apple TV generation specifications from official Apple pages.

Discovers legacy technical-specification links from Apple's model-identification page
and separately captures the newest Apple Ireland product specification page. Fails
closed when model identity or official-host checks do not pass.
"""
from __future__ import annotations
import html as html_lib, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path("apple_tv_extraction")
HTML_DIR = ROOT / "technical_specs_html"
DATA_DIR = Path("data/apple/tv")
INDEX_URL = "https://support.apple.com/en-ie/101605"
CURRENT_URL = "https://www.apple.com/ie/apple-tv-4k/specs/"
TODAY = datetime.now(timezone.utc).date().isoformat()
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TechSpecsResearch/1.0)", "Accept-Language": "en-IE,en;q=0.9"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
REPORT = {"started_utc": datetime.now(timezone.utc).isoformat(), "errors": [], "sources": [],
          "notes": ["Official Apple and Apple Support sources only.", "Original HTML responses are archived.",
                    "Source headings and visible text are preserved; missing specifications are not inferred.",
                    "Apple's current 4th-generation Apple TV 4K page is kept separate from the older model-identification list."]}

def clean(value):
    value = html_lib.unescape(value).replace("\xa0", " ")
    value = re.sub(r"[\t ]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()

def get_page(url):
    response = SESSION.get(url, timeout=45)
    response.raise_for_status()
    if "<html" not in response.text[:15000].lower():
        raise ValueError("Response did not contain an HTML document")
    host = urlparse(response.url).hostname or ""
    if urlparse(response.url).scheme != "https" or not (host == "apple.com" or host.endswith(".apple.com")):
        raise ValueError("Final URL is not an official Apple host: " + response.url)
    return response

def slugify(text):
    s = text.lower().replace("apple", "").replace("tv", "tv")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return "apple-tv-" + s

def sections_from(soup):
    sections = []
    # Preserve group-based Apple Support layouts first.
    for group in soup.select("div.gb-group"):
        heading_node = group.find(["h2", "h3", "h4"])
        if not heading_node:
            continue
        heading = clean(heading_node.get_text(" ", strip=True))
        clone = BeautifulSoup(str(group), "html.parser")
        for node in clone.find_all(["h1", "h2", "h3", "h4"]): node.decompose()
        for node in clone.select("script,style,noscript"): node.decompose()
        body = clean(clone.get_text("\n", strip=True))
        if heading and body:
            sections.append({"heading": heading, "source_text": body})
    if not sections:
        root = soup.select_one("main") or soup.select_one("article") or soup.body
        if root:
            current, chunks = None, []
            def flush():
                if current and chunks:
                    body = clean("\n".join(chunks))
                    if body: sections.append({"heading": current, "source_text": body})
            for node in root.find_all(["h1","h2","h3","h4","p","li","dt","dd"]):
                if node.name in {"h1","h2","h3","h4"}:
                    flush()
                    current, chunks = clean(node.get_text(" ", strip=True)), []
                elif current:
                    value = clean(node.get_text(" ", strip=True))
                    if value and (not chunks or chunks[-1] != value): chunks.append(value)
            flush()
    seen, unique = set(), []
    for section in sections:
        key = (section["heading"], section["source_text"])
        if key not in seen:
            seen.add(key); unique.append(section)
    return unique

def discover_targets():
    response = get_page(INDEX_URL)
    INDEX_ARCHIVE = HTML_DIR / "apple-tv-model-identification.html"
    INDEX_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_ARCHIVE.write_text(response.text, encoding="utf-8")
    soup = BeautifulSoup(response.text, "html.parser")
    discovered, seen = [], set()
    for anchor in soup.find_all("a", href=True):
        label = clean(anchor.get_text(" ", strip=True))
        if not re.search(r"tech specs for", label, re.I) or "apple tv" not in label.lower():
            continue
        url = urljoin(response.url, anchor["href"])
        if url in seen:
            continue
        seen.add(url)
        name = re.sub(r"^See the tech specs for\s+", "", label, flags=re.I).strip(" .")
        slug = slugify(name)
        discovered.append({"model": name, "slug": slug, "url": url, "source_type": "support", "year": None})
    # Always include the current product page because the support identification page can lag.
    discovered.insert(0, {"model": "Apple TV 4K (4th generation)", "slug": "apple-tv-4k-4th-generation",
                          "url": CURRENT_URL, "source_type": "manufacturer", "year": 2026})
    # Keep current generation first and deduplicate by URL/model slug.
    result, keys = [], set()
    for target in discovered:
        key = target["url"]
        if key not in keys:
            keys.add(key); result.append(target)
    return response.url, result

def identity_matches(target, title, body):
    text = clean(title + " " + body).lower()
    model = target["model"].lower()
    # Apple may use regional titles; matching model phrase anywhere in the page is the primary guard.
    if "4th generation" in model:
        return "apple tv 4k" in text and "4th generation" in text and ("a19" in text or "128gb" in text)
    phrase = model.replace("apple ", "").replace("tv ", "tv ")
    return phrase in text or model in text

def main():
    HTML_DIR.mkdir(parents=True, exist_ok=True); DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        index_final_url, targets = discover_targets()
    except Exception as exc:
        REPORT["errors"].append({"source_url": INDEX_URL, "status": "discovery_failed", "error": f"{type(exc).__name__}: {exc}"})
        targets = [{"model":"Apple TV 4K (4th generation)","slug":"apple-tv-4k-4th-generation","url":CURRENT_URL,"source_type":"manufacturer","year":2026}]
        index_final_url = INDEX_URL
    REPORT["discovery_source"] = index_final_url
    REPORT["scope_count"] = len(targets)
    for target in targets:
        item = {"model": target["model"], "requested_url": target["url"], "source_type": target["source_type"]}
        try:
            response = get_page(target["url"])
            soup = BeautifulSoup(response.text, "html.parser")
            h1 = soup.find("h1")
            title = clean(h1.get_text(" ", strip=True)) if h1 else (soup.title.get_text(" ", strip=True) if soup.title else target["model"])
            body = clean(soup.get_text(" ", strip=True))
            saved = HTML_DIR / (target["slug"] + ".html")
            saved.write_text(response.text, encoding="utf-8")
            sections = sections_from(soup)
            identity = identity_matches(target, title, body)
            item.update({"final_url": response.url, "title": title, "saved_file": saved.as_posix(),
                         "bytes": len(response.content), "section_count": len(sections), "model_identity_matches": identity})
            if not identity:
                item.update({"verification_status":"identity_not_confirmed","error":"Expected model identity not confirmed in official source; no product record written."})
                REPORT["errors"].append(item.copy())
            elif not sections:
                item.update({"verification_status":"no_sections_extracted","error":"Model identity matched but no specification sections were extracted; no product record written."})
                REPORT["errors"].append(item.copy())
            else:
                item["verification_status"] = "content_verified"
                slug = target["slug"]
                record = {
                    "schema_version":"2.0",
                    "product":{"brand":"Apple","category":"streaming-media-player","family":"Apple TV","model":target["model"],
                               "model_slug":slug,"model_year":target.get("year"),"year_introduced":target.get("year"),"variant":None},
                    "source":{"source_type":"manufacturer","source_url":response.url,"source_file":saved.as_posix(),
                              "source_title":title,"publisher":"Apple","published_at":None,"checked_at":TODAY,
                              "verification_status":"content_verified",
                              "verification_notes":f"Official Apple source captured {TODAY}; model identity confirmed in source content; {len(sections)} sections archived.",
                              "notes":["Legacy models discovered through Apple's official model-identification page." if target["source_type"]=="support" else "Current-generation specifications taken from Apple's Ireland product specification page."]},
                    "extraction":{"method":"section_preserving","normalization_status":"archival_first_pass",
                                  "note":"Original source headings and visible text retained in source order. No missing specifications inferred.",
                                  "extracted_at":TODAY,"reviewed_at":None},
                    "sections":sections,
                    "record_notes":["Archival-first-pass record generated from captured official Apple technical-specification HTML.",
                                    "No normalized specifications or missing values have been inferred."]
                }
                (DATA_DIR / (slug + ".json")).write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        except Exception as exc:
            item.update({"verification_status":"unavailable","error":f"{type(exc).__name__}: {exc}"})
            REPORT["errors"].append(item.copy())
        REPORT["sources"].append(item)
        time.sleep(0.7)
    REPORT["finished_utc"] = datetime.now(timezone.utc).isoformat()
    REPORT["summary"] = {"scope_count":len(targets),
        "pages_captured":sum(bool(x.get("saved_file")) for x in REPORT["sources"]),
        "content_verified":sum(x.get("verification_status")=="content_verified" for x in REPORT["sources"]),
        "errors":len(REPORT["errors"]),
        "specification_sections_extracted":sum(x.get("section_count",0) for x in REPORT["sources"])}
    (ROOT / "extraction_report.json").write_text(json.dumps(REPORT, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (ROOT / "discovered_urls.json").write_text(json.dumps({"discovery_source":index_final_url,
        "scope":[{"model":x["model"],"requested_url":x["url"],"verification_status":next((y.get("verification_status") for y in REPORT["sources"] if y["requested_url"]==x["url"]),"not_checked")} for x in targets]},
        ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    inventory = {"catalogue_stage":"official_apple_tv_specification_extraction","brand":"Apple","category":"streaming-media-player",
        "family":"Apple TV","market":"Ireland-facing catalogue; official Apple and Apple Support sources",
        "source_policy":"Use official Apple pages only. Preserve source text and archive HTML. Do not infer missing specifications.",
        "sources":[{"source_type":x.get("source_type"),"source_url":x.get("final_url",x["requested_url"]),"source_title":x.get("title"),
                    "publisher":"Apple","purpose":f"Technical specifications for {x['model']}",
                    "verification_status":x.get("verification_status","not_checked"),"notes":x.get("error")} for x in REPORT["sources"]],
        "working_scope":[{"model":x["model"],"record_path":f"data/apple/tv/{x['slug']}.json",
                          "source_url":x.get("final_url",x["requested_url"]),
                          "source_verification_status":x.get("verification_status","not_checked"),
                          "extraction_status":"extracted" if x.get("verification_status")=="content_verified" else "outstanding",
                          "section_count":x.get("section_count",0),"source_file":x.get("saved_file"),
                          "limitation":x.get("error")} for x in REPORT["sources"]],
        "notes":[f"Apple TV extraction run completed {TODAY}. The current 4th generation is sourced from Apple Ireland's product page; legacy generations are discovered from Apple's model-identification page."]}
    (DATA_DIR / "source-inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(REPORT["summary"], indent=2))
    for item in REPORT["sources"]:
        print(item["model"], item.get("verification_status"), "sections=", item.get("section_count",0), item.get("error",""))

if __name__ == "__main__":
    main()
