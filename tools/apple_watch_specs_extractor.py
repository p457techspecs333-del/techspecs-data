#!/usr/bin/env python3
"""Capture and section-preserve official Apple Watch technical-specification pages."""
from __future__ import annotations
import json, re, time, html as html_lib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

ROOT=Path("apple_watch_extraction"); HTML_DIR=ROOT/"technical_specs_html"
DATA_DIR=Path("data/apple/watch"); INVENTORY=DATA_DIR/"source-inventory.json"
TODAY=datetime.now(timezone.utc).date().isoformat()
TARGETS=[
("apple-watch-series-12","Apple Watch Series 12",2026,"https://www.apple.com/apple-watch-series-12/specs/"),
("apple-watch-series-11","Apple Watch Series 11",2025,"https://support.apple.com/en-ie/125093"),
("apple-watch-series-10","Apple Watch Series 10",2024,"https://support.apple.com/en-ie/121202"),
("apple-watch-series-9","Apple Watch Series 9",2023,"https://support.apple.com/en-lb/111833"),
("apple-watch-series-8","Apple Watch Series 8",2022,"https://support.apple.com/en-ie/111848"),
("apple-watch-se-3","Apple Watch SE 3",2025,"https://support.apple.com/en-ie/125094"),
("apple-watch-se-2","Apple Watch SE (2nd generation)",2022,"https://support.apple.com/en-by/111853"),
("apple-watch-ultra-4","Apple Watch Ultra 4",2026,"https://www.apple.com/apple-watch-ultra-4/specs/"),
("apple-watch-ultra-3","Apple Watch Ultra 3",2025,"https://support.apple.com/en-ie/125095"),
("apple-watch-ultra-2","Apple Watch Ultra 2",2023,"https://support.apple.com/en-ie/111832")]
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36","Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"en-IE,en;q=0.9,en-GB;q=0.8"})
report={"started_utc":datetime.now(timezone.utc).isoformat(),"scope_count":len(TARGETS),"sources":[],"errors":[],"notes":["Official Apple and Apple Support pages only.","Original response HTML is archived before extraction.","A resolving URL alone is not content verification.","Records are updated only when the page identifies the expected model and yields actual specification sections.","Original headings and visible source text are preserved; missing values are not inferred."]}

def clean(v):
    v=html_lib.unescape(v).replace("\xa0"," ")
    v=re.sub(r"[\t ]+"," ",v); v=re.sub(r" *\n *","\n",v); v=re.sub(r"\n{3,}","\n\n",v)
    return v.strip()

def sections(soup):
    out=[]
    for group in soup.select("div.gb-group"):
        h=group.find(["h2","h3","h4"])
        if not h: continue
        heading=clean(h.get_text(" ",strip=True)); body=BeautifulSoup(str(group),"html.parser")
        for n in body.find_all(["h2","h3","h4"]): n.decompose()
        for n in body.select("script,style,noscript"): n.decompose()
        txt=clean(body.get_text("\n",strip=True))
        if heading and txt: out.append({"heading":heading,"source_text":txt})
    if not out:
        root=soup.select_one("main") or soup.select_one("article") or soup.body
        if root:
            current=None; chunks=[]
            for node in root.find_all(["h1","h2","h3","h4","p","li","dt","dd"]):
                if node.name in {"h1","h2","h3","h4"}:
                    if current and chunks:
                        txt=clean("\n".join(chunks))
                        if txt: out.append({"heading":current,"source_text":txt})
                    current=clean(node.get_text(" ",strip=True)); chunks=[]
                elif current:
                    txt=clean(node.get_text(" ",strip=True))
                    if txt and (not chunks or chunks[-1]!=txt): chunks.append(txt)
            if current and chunks:
                txt=clean("\n".join(chunks))
                if txt: out.append({"heading":current,"source_text":txt})
    unique=[]; seen=set()
    for x in out:
        k=(x["heading"],x["source_text"])
        if k not in seen: seen.add(k); unique.append(x)
    return unique

def matches(text,expected):
    t=re.sub(r"[^a-z0-9]+"," ",text.lower()); e=re.sub(r"[^a-z0-9]+"," ",expected.lower())
    if expected.startswith("Apple Watch SE"):
        return "apple watch se" in t and (("3" in t) if "SE 3" in expected else ("2nd generation" in t or "2" in t))
    return e in t

def main():
    HTML_DIR.mkdir(parents=True,exist_ok=True); results=[]
    for slug,expected,year,url in TARGETS:
        item={"model":expected,"model_slug":slug,"requested_url":url}
        try:
            response=None
            for attempt in range(4):
                try:
                    response=session.get(url,timeout=40)
                    if response.status_code==200 and "<html" in response.text[:10000].lower(): break
                    if response.status_code not in (429,500,502,503,504): break
                except requests.RequestException as exc: item["error"]=str(exc)
                if attempt<3: time.sleep(2*(attempt+1))
            if response is None:
                item.update({"verification_status":"unavailable","error":item.get("error","No HTTP response")})
                report["errors"].append(item.copy()); results.append(item); continue
            item.update({"status":response.status_code,"final_url":response.url})
            if response.status_code!=200 or "<html" not in response.text[:10000].lower():
                item.update({"verification_status":"unavailable","error":f"Apple returned HTTP {response.status_code}; no HTML archived."})
                report["errors"].append(item.copy()); results.append(item); continue
            host=urlparse(response.url).hostname
            if urlparse(response.url).scheme!="https" or host not in {"support.apple.com","www.apple.com","apple.com"}:
                item.update({"verification_status":"unavailable","error":"Final URL is not an official Apple host."})
                report["errors"].append(item.copy()); results.append(item); continue
            saved=HTML_DIR/f"{slug}.html"; saved.write_text(response.text,encoding="utf-8")
            soup=BeautifulSoup(response.text,"html.parser"); h1=soup.find("h1")
            title=clean(h1.get_text(" ",strip=True)) if h1 else (soup.title.get_text(" ",strip=True) if soup.title else "")
            extracted=sections(soup); identity=matches(title+" "+response.url,expected)
            item.update({"title":title,"saved_file":saved.as_posix(),"bytes":len(response.content),"section_count":len(extracted),"model_identity_matches":identity})
            if not identity:
                item.update({"verification_status":"conflicting_sources","error":"Page identity did not match expected model; record left unchanged."})
                report["errors"].append(item.copy())
            elif not extracted:
                item.update({"verification_status":"partially_verified","error":"Page captured but no specification sections extracted; record left unchanged."})
                report["errors"].append(item.copy())
            else:
                item["verification_status"]="content_verified"
                path=DATA_DIR/f"{slug}.json"; record=json.loads(path.read_text(encoding="utf-8"))
                record["source"].update({"source_url":response.url,"source_file":saved.as_posix(),"source_title":title,"publisher":"Apple" if host in {"www.apple.com","apple.com"} else "Apple Support","checked_at":TODAY,"verification_status":"content_verified","verification_notes":f"Official Apple page captured {TODAY}; page identity matched {expected}; {len(extracted)} source sections extracted and archived at {saved.as_posix()}."})
                record["extraction"].update({"method":"section_preserving","normalization_status":"archival_first_pass","note":"Apple's original section headings and visible source text are retained in source order from captured official HTML. No normalized values or missing specifications have been inferred.","extracted_at":TODAY,"reviewed_at":None})
                record["sections"]=extracted
                record["record_notes"]=["Archival-first-pass record generated from captured official Apple technical-specification HTML.","Original Apple section headings and visible source text are retained. No normalized specifications have been inferred.","Case size, finish and GPS/cellular configurations remain within this model record unless later evidence establishes a meaningful separate product."]
                path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            results.append(item); time.sleep(1)
        except Exception as exc:
            item.update({"verification_status":"unavailable","error":f"{type(exc).__name__}: {exc}"})
            report["errors"].append(item.copy()); results.append(item)
    report["sources"]=results; report["finished_utc"]=datetime.now(timezone.utc).isoformat()
    report["summary"]={"scope_count":len(TARGETS),"pages_captured":sum(bool(x.get("saved_file")) for x in results),"content_verified":sum(x.get("verification_status")=="content_verified" for x in results),"partially_verified":sum(x.get("verification_status")=="partially_verified" for x in results),"conflicting_or_unavailable":sum(x.get("verification_status") in {"conflicting_sources","unavailable"} for x in results),"specification_sections_extracted":sum(x.get("section_count",0) for x in results)}
    (ROOT/"extraction_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"discovered_urls.json").write_text(json.dumps({"scope":[{"model":x["model"],"requested_url":x["requested_url"],"final_url":x.get("final_url"),"verification_status":x.get("verification_status")} for x in results]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    inv=json.loads(INVENTORY.read_text(encoding="utf-8")); inv["catalogue_stage"]="official_watch_specification_extraction"
    inv["working_scope"]=[{"model":x["model"],"record_path":f"data/apple/watch/{x['model_slug']}.json","source_url":x.get("final_url",x["requested_url"]),"source_verification_status":x.get("verification_status","not_checked"),"extraction_status":"extracted" if x.get("section_count",0)>0 and x.get("model_identity_matches") else "outstanding","section_count":x.get("section_count",0),"source_file":x.get("saved_file"),"limitation":x.get("error")} for x in results]
    inv["notes"]=[n for n in inv.get("notes",[]) if "Next step is to collect official Apple product/specification URLs" not in n]
    inv["notes"].append(f"Ten-model Watch extraction run completed {TODAY}. See apple_watch_extraction/extraction_report.json; incomplete pages are not labelled complete.")
    INVENTORY.write_text(json.dumps(inv,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report["summary"],indent=2))
    for x in results: print(x["model"],x.get("verification_status"),"sections=",x.get("section_count",0),x.get("error",""))

if __name__=="__main__": main()
