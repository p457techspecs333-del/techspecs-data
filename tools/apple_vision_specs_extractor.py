#!/usr/bin/env python3
"""Capture official Apple Vision Pro M2 and M5 specifications into TechSpecs v2 records."""
from __future__ import annotations
import json, re, time, html as html_lib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

ROOT=Path("apple_vision_extraction")
HTML_DIR=ROOT/"technical_specs_html"
DATA_DIR=Path("data/apple/vision")
INVENTORY=DATA_DIR/"source-inventory.json"
TODAY=datetime.now(timezone.utc).date().isoformat()
TARGETS=[
 {"slug":"apple-vision-pro-m2","model":"Apple Vision Pro (M2)","family":"Apple Vision Pro","year":2024,"chip":"Apple M2 Chip","url":"https://support.apple.com/en-ie/117810"},
 {"slug":"apple-vision-pro-m5","model":"Apple Vision Pro (M5)","family":"Apple Vision Pro","year":2025,"chip":"Apple M5 chip","url":"https://support.apple.com/en-ie/125436"}
]
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36","Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"en-IE,en;q=0.9,en-GB;q=0.8"})
report={"started_utc":datetime.now(timezone.utc).isoformat(),"scope_count":len(TARGETS),"sources":[],"errors":[],"notes":["Official Apple and Apple Support pages only.","Original response HTML is archived before extraction.","Page identity is verified against year and chip generation, not title alone.","Original section headings and visible text are retained; missing values are not inferred."]}

def clean(v):
 v=html_lib.unescape(v).replace("\xa0"," ")
 v=re.sub(r"[\t ]+"," ",v); v=re.sub(r" *\n *","\n",v); v=re.sub(r"\n{3,}","\n\n",v)
 return v.strip()

def extract_sections(soup):
 out=[]
 # Apple Support's technical specifications pages usually use gb-group containers.
 for group in soup.select("div.gb-group"):
  h=group.find(["h2","h3","h4"])
  if not h: continue
  heading=clean(h.get_text(" ",strip=True)); body=BeautifulSoup(str(group),"html.parser")
  for n in body.find_all(["h2","h3","h4"]): n.decompose()
  for n in body.select("script,style,noscript"): n.decompose()
  txt=clean(body.get_text("\n",strip=True))
  if heading and txt: out.append({"heading":heading,"source_text":txt})
 # Fallback for older Apple page layouts.
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

def identity_ok(text,target):
 t=re.sub(r"[^a-z0-9]+"," ",text.lower())
 return str(target["year"]) in t and target["chip"].lower() in text.lower() and "apple vision pro" in t

def record_for(target,url,title,source_file,sections):
 return {
  "schema_version":"2.0",
  "product":{"brand":"Apple","category":"spatial-computing-headset","family":target["family"],"model":target["model"],"model_slug":target["slug"],"model_year":target["year"],"year_introduced":target["year"],"variant":target["chip"]},
  "source":{"source_type":"manufacturer","source_url":url,"source_file":source_file,"source_title":title,"publisher":"Apple Support","published_at":None,"checked_at":TODAY,"verification_status":"content_verified","verification_notes":f"Official Apple Support page captured {TODAY}; year {target['year']} and {target['chip']} verified in source content; {len(sections)} sections archived at {source_file}.","notes":[]},
  "extraction":{"method":"section_preserving","normalization_status":"archival_first_pass","note":"Apple's original section headings and visible source text are retained in source order from captured official HTML. No normalized values or missing specifications have been inferred.","extracted_at":TODAY,"reviewed_at":None},
  "sections":sections,
  "record_notes":["Archival-first-pass record generated from captured official Apple technical-specification HTML.","Original Apple section headings and visible source text are retained. No normalized specifications have been inferred.","M2 and M5 generations are separate records because Apple publishes distinct chip generations and specification pages."]
 }

def main():
 HTML_DIR.mkdir(parents=True,exist_ok=True); DATA_DIR.mkdir(parents=True,exist_ok=True); results=[]
 for target in TARGETS:
  item={"model":target["model"],"model_slug":target["slug"],"requested_url":target["url"]}
  try:
   response=None
   for attempt in range(4):
    try:
     response=session.get(target["url"],timeout=40)
     if response.status_code==200 and "<html" in response.text[:10000].lower(): break
     if response.status_code not in (429,500,502,503,504): break
    except requests.RequestException as exc: item["error"]=str(exc)
    if attempt<3: time.sleep(2*(attempt+1))
   if response is None:
    item.update({"verification_status":"unavailable","error":item.get("error","No HTTP response")}); report["errors"].append(item.copy()); results.append(item); continue
   item.update({"status":response.status_code,"final_url":response.url})
   if response.status_code!=200 or "<html" not in response.text[:10000].lower():
    item.update({"verification_status":"unavailable","error":f"Apple returned HTTP {response.status_code}; no HTML archived."}); report["errors"].append(item.copy()); results.append(item); continue
   host=urlparse(response.url).hostname
   if urlparse(response.url).scheme!="https" or host not in {"support.apple.com","www.apple.com","apple.com"}:
    item.update({"verification_status":"unavailable","error":"Final URL is not an official Apple host."}); report["errors"].append(item.copy()); results.append(item); continue
   saved=HTML_DIR/f"{target['slug']}.html"; saved.write_text(response.text,encoding="utf-8")
   soup=BeautifulSoup(response.text,"html.parser"); h1=soup.find("h1")
   title=clean(h1.get_text(" ",strip=True)) if h1 else (soup.title.get_text(" ",strip=True) if soup.title else "")
   body_text=clean(soup.get_text(" ",strip=True)); extracted=extract_sections(soup)
   identity=identity_ok(title+" "+body_text,target)
   item.update({"title":title,"saved_file":saved.as_posix(),"bytes":len(response.content),"section_count":len(extracted),"model_identity_matches":identity})
   if not identity:
    item.update({"verification_status":"conflicting_sources","error":"Page content did not confirm the expected Vision Pro generation and chip; product record left unchanged."}); report["errors"].append(item.copy())
   elif not extracted:
    item.update({"verification_status":"partially_verified","error":"Page identity matched, but no specification sections were extracted; product record left unchanged."}); report["errors"].append(item.copy())
   else:
    item["verification_status"]="content_verified"
    rec=record_for(target,response.url,title,saved.as_posix(),extracted)
    (DATA_DIR/f"{target['slug']}.json").write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
   results.append(item); time.sleep(1)
  except Exception as exc:
   item.update({"verification_status":"unavailable","error":f"{type(exc).__name__}: {exc}"}); report["errors"].append(item.copy()); results.append(item)
 report["sources"]=results; report["finished_utc"]=datetime.now(timezone.utc).isoformat()
 report["summary"]={"scope_count":len(TARGETS),"pages_captured":sum(bool(x.get("saved_file")) for x in results),"content_verified":sum(x.get("verification_status")=="content_verified" for x in results),"partially_verified":sum(x.get("verification_status")=="partially_verified" for x in results),"conflicting_or_unavailable":sum(x.get("verification_status") in {"conflicting_sources","unavailable"} for x in results),"specification_sections_extracted":sum(x.get("section_count",0) for x in results)}
 (ROOT/"extraction_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (ROOT/"discovered_urls.json").write_text(json.dumps({"scope":[{"model":x["model"],"requested_url":x["requested_url"],"final_url":x.get("final_url"),"verification_status":x.get("verification_status")} for x in results]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 inventory={"catalogue_stage":"official_vision_pro_specification_extraction","brand":"Apple","category":"spatial-computing-headset","family":"Apple Vision Pro","market":"Ireland-facing catalogue; official Apple and Apple Support sources","source_policy":"Use official Apple/Apple Support specification pages. Preserve original source text and archive HTML. Do not create separate records for storage or fit accessories unless the manufacturer treats them as distinct product generations.","sources":[{"source_type":"manufacturer","source_url":x.get("final_url",x["requested_url"]),"source_title":x.get("title"),"publisher":"Apple Support","purpose":f"Technical specifications for {x['model']}","verification_status":x.get("verification_status","not_checked"),"notes":x.get("error")} for x in results],"working_scope":[{"model":x["model"],"record_path":f"data/apple/vision/{x['model_slug']}.json","source_url":x.get("final_url",x["requested_url"]),"source_verification_status":x.get("verification_status","not_checked"),"extraction_status":"extracted" if x.get("section_count",0)>0 and x.get("model_identity_matches") else "outstanding","section_count":x.get("section_count",0),"source_file":x.get("saved_file"),"limitation":x.get("error")} for x in results],"notes":[f"Two-generation Apple Vision Pro extraction run completed {TODAY}. See apple_vision_extraction/extraction_report.json."] }
 (DATA_DIR/"source-inventory.json").write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report["summary"],indent=2))
 for x in results: print(x["model"],x.get("verification_status"),"sections=",x.get("section_count",0),x.get("error",""))
if __name__=="__main__": main()
