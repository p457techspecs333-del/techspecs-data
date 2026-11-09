#!/usr/bin/env python3
"""Discover and archive official Apple specs/manuals for remaining product families.

Uses Apple Support model-identification pages and Apple's documentation hub.
Only HTTPS Apple-owned pages are accepted. A product record is written only when
a page has a plausible model identity and useful visible specification content.
"""
from __future__ import annotations
import html as html_lib, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

TODAY = datetime.now(timezone.utc).date().isoformat()
BASE = Path("apple_remaining_extraction")
ARCHIVE = BASE / "technical_specs_html"
ROOT = Path("data/apple")
HEADERS = {"User-Agent":"Mozilla/5.0 (compatible; TechSpecsResearch/1.0)","Accept-Language":"en-IE,en;q=0.9"}
S = requests.Session(); S.headers.update(HEADERS)
FAMILIES = [
 {"key":"airpods","label":"AirPods","category":"audio","index":"https://support.apple.com/en-ie/109525","kind":"hardware"},
 {"key":"homepod","label":"HomePod","category":"smart-speaker","index":"https://support.apple.com/en-gb/101609","kind":"hardware"},
 {"key":"ipod","label":"iPod","category":"portable-media-player","index":"https://support.apple.com/en-ie/103823","kind":"hardware"},
 {"key":"displays","label":"Apple Displays","category":"computer-display","index":"https://support.apple.com/en-ie/126265","kind":"hardware"},
 {"key":"accessories","label":"Apple Accessories","category":"accessory","index":"https://support.apple.com/en-ie/docs/accessories","kind":"catalogue"},
 {"key":"software","label":"Apple Software","category":"software","index":"https://support.apple.com/en-ie/docs/software","kind":"catalogue"},
]
REPORT={"started_utc":datetime.now(timezone.utc).isoformat(),"families":[],"notes":[
 "Official Apple/Apple Support sources only; original HTML archived.",
 "No missing technical details are inferred. Hardware records preserve source headings and text.",
 "Accessories and software are broad catalogues, not single hardware model families; their official indexes are archived and linked records are inventoried separately."]}
def clean(v):
 v=html_lib.unescape(v).replace("\xa0"," ")
 v=re.sub(r"[\t ]+"," ",v); v=re.sub(r" *\n *","\n",v); v=re.sub(r"\n{3,}","\n\n",v)
 return v.strip()
def get(url):
 r=S.get(url,timeout=45); r.raise_for_status()
 if "<html" not in r.text[:20000].lower(): raise ValueError("No HTML document")
 p=urlparse(r.url); host=p.hostname or ""
 if p.scheme!="https" or not (host=="apple.com" or host.endswith(".apple.com")): raise ValueError("Not official Apple host: "+r.url)
 return r
def slug(s):
 return re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",s.lower())).strip("-")[:110]
def sections(soup):
 out=[]
 for group in soup.select("div.gb-group"):
  h=group.find(["h2","h3","h4"])
  if not h: continue
  clone=BeautifulSoup(str(group),"html.parser")
  for n in clone.find_all(["h1","h2","h3","h4"]): n.decompose()
  for n in clone.select("script,style,noscript"): n.decompose()
  body=clean(clone.get_text("\n",strip=True)); heading=clean(h.get_text(" ",strip=True))
  if body: out.append({"heading":heading,"source_text":body})
 if not out:
  root=soup.select_one("main") or soup.select_one("article") or soup.body
  current=None; chunks=[]
  def flush():
   if current and chunks:
    body=clean("\n".join(chunks))
    if body: out.append({"heading":current,"source_text":body})
  if root:
   for n in root.find_all(["h1","h2","h3","h4","p","li","dt","dd"]):
    if n.name in {"h1","h2","h3","h4"}:
     flush(); current=clean(n.get_text(" ",strip=True)); chunks=[]
    elif current:
     t=clean(n.get_text(" ",strip=True))
     if t and (not chunks or chunks[-1]!=t): chunks.append(t)
   flush()
 seen=set(); result=[]
 for x in out:
  k=(x["heading"],x["source_text"])
  if k not in seen: seen.add(k); result.append(x)
 return result
def family_targets(f,soup,final_url):
 targets=[]; seen=set()
 if f["key"]=="airpods":
  explicit=[
   {"model":"AirPods 5","url":"https://www.apple.com/ie/airpods-5/specs/"},
   {"model":"AirPods Pro 3","url":"https://support.apple.com/en-ie/125135"},
   {"model":"AirPods 4","url":"https://support.apple.com/en-ie/121203"},
   {"model":"AirPods 4 with Active Noise Cancellation","url":"https://support.apple.com/en-ie/121204"},
   {"model":"AirPods Max 2","url":"https://www.apple.com/ie/airpods-max/specs/"},
  ]
  for t in explicit: t["slug"]=slug(t["model"])
  return explicit
 # Model identification pages link to product-specific specs. Accept clearly labelled spec links.
 for a in soup.find_all("a",href=True):
  label=clean(a.get_text(" ",strip=True)); url=urljoin(final_url,a["href"])
  if not label or url in seen: continue
  low=label.lower()
  relevant=(("tech spec" in low or "technical specification" in low) and
    (f["label"].lower().split()[0] in low or f["key"]=="displays" and ("display" in low or "studio display" in low)))
  if relevant and urlparse(url).hostname and (urlparse(url).hostname=="apple.com" or urlparse(url).hostname.endswith(".apple.com")):
   seen.add(url); name=re.sub(r"^(?:see\s+)?(?:the\s+)?tech specs for\s+","",label,flags=re.I).strip(" .")
   targets.append({"model":name or label,"url":url,"slug":slug(name or label)})
 # Apple's documentation hub may link product-family index pages; retain as inventory links, not product records.
 return targets
def main():
 ARCHIVE.mkdir(parents=True,exist_ok=True)
 for f in FAMILIES:
  item={"key":f["key"],"label":f["label"],"index_url":f["index"],"status":"pending","targets":[],"errors":[]}
  family_dir=ROOT/f["key"]; family_dir.mkdir(parents=True,exist_ok=True)
  try:
   r=get(f["index"]); soup=BeautifulSoup(r.text,"html.parser")
   index_file=ARCHIVE/(f["key"]+"-index.html"); index_file.write_text(r.text,encoding="utf-8")
   item.update({"final_index_url":r.url,"index_title":clean(soup.title.get_text(" ",strip=True)) if soup.title else f["label"],
                "index_archive":index_file.as_posix(),"index_bytes":len(r.content)})
   targets=family_targets(f,soup,r.url)
   for t in targets:
    row={"model":t["model"],"url":t["url"],"slug":t["slug"]}
    try:
     page=get(t["url"]); ps=BeautifulSoup(page.text,"html.parser")
     h=ps.find("h1"); title=clean(h.get_text(" ",strip=True)) if h else (clean(ps.title.get_text(" ",strip=True)) if ps.title else t["model"])
     sec=sections(ps); body=clean(ps.get_text(" ",strip=True))
     identity=bool(re.search(re.escape(t["model"][:18]),title+" "+body,re.I)) or bool(re.search(r"specification|technical specifications|tech specs",title,re.I))
     saved=ARCHIVE/(f["key"]+"-"+t["slug"]+".html"); saved.write_text(page.text,encoding="utf-8")
     row.update({"final_url":page.url,"title":title,"source_file":saved.as_posix(),"section_count":len(sec),
                 "verification_status":"content_verified" if sec and identity else "needs_review"})
     if sec and identity:
      record={"schema_version":"2.0","product":{"brand":"Apple","category":f["category"],"family":f["label"],
       "model":t["model"],"model_slug":t["slug"],"model_year":None,"year_introduced":None,"variant":None},
       "source":{"source_type":"manufacturer","source_url":page.url,"source_file":saved.as_posix(),"source_title":title,
        "publisher":"Apple","published_at":None,"checked_at":TODAY,"verification_status":"content_verified",
        "verification_notes":f"Official Apple source captured {TODAY}; source headings and {len(sec)} sections archived.",
        "notes":["Extracted from official Apple technical specification link discovered on model index."]},
       "extraction":{"method":"section_preserving","normalization_status":"archival_first_pass",
        "note":"Source headings and visible text retained; no missing specifications inferred.","extracted_at":TODAY,"reviewed_at":None},
       "sections":sec,"record_notes":["Archival-first-pass record; normalized specifications not inferred."]}
      (family_dir/(t["slug"]+".json")).write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    except Exception as e: row.update({"verification_status":"unavailable","error":f"{type(e).__name__}: {e}"}); item["errors"].append(row.copy())
    item["targets"].append(row); time.sleep(.4)
   item["status"]="index_captured"
   if f["kind"]=="hardware" and not targets: item["status"]="index_captured_no_spec_links"
  except Exception as e:
   item.update({"status":"index_failed","error":f"{type(e).__name__}: {e}"}); item["errors"].append({"url":f["index"],"error":item["error"]})
  item["summary"]={"spec_links_discovered":len(item["targets"]),"records_written":sum(x.get("verification_status")=="content_verified" for x in item["targets"]),
                   "needs_review":sum(x.get("verification_status")=="needs_review" for x in item["targets"]),"errors":len(item["errors"])}
  inventory={"catalogue_stage":"official_apple_source_discovery","brand":"Apple","category":f["category"],"family":f["label"],
   "market":"Ireland-facing catalogue","source_policy":"Official Apple sources only; preserve original HTML; no inferred specifications.",
   "index_url":item.get("final_index_url",f["index"]),"index_title":item.get("index_title"),"index_archive":item.get("index_archive"),
   "working_scope":item["targets"],"notes":[f"Discovery checked {TODAY}. This is an initial source-discovery inventory; coverage is not claimed complete."]}
  (family_dir/"source-inventory.json").write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  REPORT["families"].append(item)
  print(f'{f["label"]}: {item["status"]}; links={len(item["targets"])}; records={item["summary"]["records_written"]}; errors={len(item["errors"])}')
 REPORT["finished_utc"]=datetime.now(timezone.utc).isoformat()
 REPORT["summary"]={"families_checked":len(REPORT["families"]),"indexes_captured":sum(bool(x.get("index_archive")) for x in REPORT["families"]),
  "spec_links_discovered":sum(len(x.get("targets",[])) for x in REPORT["families"]),
  "records_written":sum(x.get("summary",{}).get("records_written",0) for x in REPORT["families"]),
  "errors":sum(len(x.get("errors",[])) for x in REPORT["families"])}
 (BASE/"extraction_report.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(REPORT["summary"],indent=2))
if __name__=="__main__": main()
