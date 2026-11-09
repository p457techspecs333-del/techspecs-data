#!/usr/bin/env python3
"""Second-pass discovery: follow Apple product documentation pages to Tech Specs, including AirPods."""
from __future__ import annotations
import concurrent.futures, html, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

TODAY=datetime.now(timezone.utc).date().isoformat()
ROOT=Path("data/apple"); ARCHIVE=Path("apple_remaining_extraction/technical_specs_html")
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; TechSpecsResearch/1.0)","Accept-Language":"en-IE,en;q=0.9"}
def clean(v):
 v=html.unescape(v).replace("\xa0"," ")
 v=re.sub(r"[\t ]+"," ",v); v=re.sub(r" *\n *","\n",v); v=re.sub(r"\n{3,}","\n\n",v)
 return v.strip()
def slug(s): return re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",s.lower())).strip("-")[:110]
def get(url):
 r=requests.get(url,headers=HEADERS,timeout=20); r.raise_for_status()
 if "<html" not in r.text[:20000].lower(): raise ValueError("No HTML document")
 p=urlparse(r.url); host=p.hostname or ""
 if p.scheme!="https" or not (host=="apple.com" or host.endswith(".apple.com")): raise ValueError("Not official Apple host")
 return r
def sections(soup):
 out=[]
 for group in soup.select("div.gb-group"):
  h=group.find(["h2","h3","h4"])
  if not h: continue
  clone=BeautifulSoup(str(group),"html.parser")
  for n in clone.find_all(["h1","h2","h3","h4"]): n.decompose()
  for n in clone.select("script,style,noscript"): n.decompose()
  body=clean(clone.get_text("\n",strip=True))
  if body: out.append({"heading":clean(h.get_text(" ",strip=True)),"source_text":body})
 if not out:
  root=soup.select_one("main") or soup.select_one("article") or soup.body
  current=None; chunks=[]
  def flush():
   if current and chunks:
    body=clean("\n".join(chunks))
    if body: out.append({"heading":current,"source_text":body})
  if root:
   for n in root.find_all(["h1","h2","h3","h4","p","li","dt","dd"]):
    if n.name in {"h1","h2","h3","h4"}: flush(); current=clean(n.get_text(" ",strip=True)); chunks=[]
    elif current:
     t=clean(n.get_text(" ",strip=True))
     if t and (not chunks or chunks[-1]!=t): chunks.append(t)
   flush()
 seen=set(); res=[]
 for x in out:
  k=(x["heading"],x["source_text"])
  if k not in seen: seen.add(k); res.append(x)
 return res
def process(args):
 family,label,url=args
 result={"family":family,"label":label,"documentation_url":url,"status":"pending"}
 try:
  doc=get(url); soup=BeautifulSoup(doc.text,"html.parser")
  h=soup.find("h1"); model=clean(h.get_text(" ",strip=True)) if h else label
  body=clean(soup.get_text(" ",strip=True))
  year_match=re.search(r"Year introduced:\s*(\d{4})",body,re.I)
  doc_archive=ARCHIVE/(family+"-docs-"+slug(label)+".html")
  doc_archive.parent.mkdir(parents=True,exist_ok=True); doc_archive.write_text(doc.text,encoding="utf-8")
  specs=[]
  for a in soup.find_all("a",href=True):
   link_label=clean(a.get_text(" ",strip=True))
   if re.search(r"tech\s*spec|technical specifications",link_label,re.I):
    target=urljoin(doc.url,a["href"]); host=urlparse(target).hostname or ""
    if host=="apple.com" or host.endswith(".apple.com"):
     if target not in [x["url"] for x in specs]: specs.append({"label":link_label,"url":target})
  result.update({"final_documentation_url":doc.url,"model":model,"year_introduced":int(year_match.group(1)) if year_match else None,
                 "documentation_archive":doc_archive.as_posix(),"spec_links":specs,"status":"documentation_captured"})
  result["records"]=[]
  for spec in specs:
   try:
    page=get(spec["url"]); ps=BeautifulSoup(page.text,"html.parser")
    sh=ps.find("h1"); title=clean(sh.get_text(" ",strip=True)) if sh else spec["label"]
    sec=sections(ps)
    saved=ARCHIVE/(family+"-specs-"+slug(model)+"-"+slug(title)+".html")
    saved.write_text(page.text,encoding="utf-8")
    if not sec:
     result["records"].append({"url":page.url,"title":title,"status":"no_sections_extracted"}); continue
    record={"schema_version":"2.0","product":{"brand":"Apple","category":"accessory" if family=="accessories" else "software",
      "family":"Apple Accessories" if family=="accessories" else "Apple Software","model":model,"model_slug":(slug(model) if family=="accessories" else slug(model)+"--"+slug(title)+"--"+slug(urlparse(page.url).path.rstrip("/").split("/")[-1])),
      "model_year":(int(year_match.group(1)) if year_match and int(year_match.group(1)) >= 2007 else None),"year_introduced":(int(year_match.group(1)) if year_match and int(year_match.group(1)) >= 2007 else None),"variant":None},
      "source":{"source_type":"manufacturer","source_url":page.url,"source_file":saved.as_posix(),"source_title":title,"publisher":"Apple",
       "published_at":None,"checked_at":TODAY,"verification_status":"content_verified",
       "verification_notes":f"Official Apple technical-specification page discovered from its documentation index; {len(sec)} sections archived.",
       "notes":[f"Documentation index: {doc.url}"]},
      "extraction":{"method":"section_preserving","normalization_status":"archival_first_pass",
       "note":"Original specification headings and visible text retained; no missing specifications inferred.","extracted_at":TODAY,"reviewed_at":None},
      "sections":sec,"record_notes":["Archival-first-pass technical specification record; normalized values not inferred."]}
    record_key=slug(model) if family=="accessories" else slug(model)+"--"+slug(title)+"--"+slug(urlparse(page.url).path.rstrip("/").split("/")[-1])
    out=ROOT/family/(record_key+".json"); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    result["records"].append({"url":page.url,"title":title,"status":"content_verified","section_count":len(sec),"record_path":out.as_posix()})
   except Exception as e: result["records"].append({"url":spec["url"],"status":"unavailable","error":f"{type(e).__name__}: {e}"})
 except Exception as e: result.update({"status":"unavailable","error":f"{type(e).__name__}: {e}"})
 return result
def main():
 ARCHIVE.mkdir(parents=True,exist_ok=True); jobs=[]
 # Remove superseded simple AirPods records; the second-pass files preserve each distinct official spec page.
 airpods_dir=ROOT/"airpods"
 if airpods_dir.exists():
  for stale in airpods_dir.glob("*.json"):
   if stale.name!="source-inventory.json" and "--" not in stale.stem: stale.unlink()
 # Replace software records from this extractor so every distinct official spec page is retained.
 software_dir=ROOT/"software"
 if software_dir.exists():
  for stale in software_dir.glob("*.json"):
   if stale.name!="source-inventory.json": stale.unlink()
 for family in ("airpods","accessories","software"):
  p=ROOT/family/"source-inventory.json"
  if not p.exists(): continue
  inv=json.loads(p.read_text(encoding="utf-8"))
  for item in inv.get("catalogue_links",[]):
   url=item.get("url","")
   if f"/docs/{family}/" in url and urlparse(url).hostname=="support.apple.com":
    jobs.append((family,item.get("label",""),url))
 # Keep only product pages with stable doc IDs; deduplicate by URL.
 seen=set(); jobs=[x for x in jobs if not (x[2] in seen or seen.add(x[2]))]
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for item in pool.map(process,jobs): results.append(item)
 report={"started_utc":datetime.now(timezone.utc).isoformat(),"finished_utc":datetime.now(timezone.utc).isoformat(),
  "documentation_pages_checked":len(results),"technical_spec_links_discovered":sum(len(x.get("spec_links",[])) for x in results),
  "records_written":sum(sum(y.get("status")=="content_verified" for y in x.get("records",[])) for x in results),
  "errors":sum(x.get("status")=="unavailable" for x in results)+sum(y.get("status")=="unavailable" for x in results for y in x.get("records",[])),
  "pages":results}
 out=Path("apple_remaining_extraction/secondary_extraction_report.json")
 out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({k:report[k] for k in ("documentation_pages_checked","technical_spec_links_discovered","records_written","errors")},indent=2))
if __name__=="__main__": main()
