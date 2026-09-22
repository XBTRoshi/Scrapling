#!/usr/bin/env python3
import json, re, subprocess, sys, time
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT=Path(__file__).parent
OUT=ROOT/"results"
EVID=OUT/"evidence"
OUT.mkdir(exist_ok=True); EVID.mkdir(exist_ok=True)
sites=json.loads((ROOT/"sites.example.json").read_text())["sites"]
signals=json.loads((ROOT/"signal_catalog.json").read_text())["signals"]

PRICE_RE=re.compile(r'(?:(?:USD|US\$|\$)\s?\d{1,5}(?:[.,]\d{2})?)')
PCT_RE=re.compile(r'\b\d{1,2}%\b')
KEYWORDS={
 "promotion_text":["sale","save ","off","discount","limited time","offer"],
 "bundle_offer":["bundle","multipack","multi-pack","build a bundle"],
 "subscription_available":["subscribe","subscription","autoship","auto-ship"],
 "shipping_offer":["free shipping","shipping"],
 "free_shipping_threshold":["free shipping on","free shipping over","free shipping for orders"],
 "stock_status":["in stock","out of stock","sold out"],
 "bestseller_status":["best seller","bestseller","best-selling"],
 "announcement_bar":["free shipping","sale","save ","off","limited time"],
 "sale_launch_blocks":["new","launch","sale"],
 "review_text":["review","reviews"],
}

def run(cmd, timeout=90):
    p=subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    return p.returncode,p.stdout[-4000:],p.stderr[-4000:]

def fetch(url, stem, mode="get"):
    path=EVID/f"{stem}-{mode}.html"
    cmd=["scrapling","extract",mode,url,str(path),"--timeout","45"]
    if mode in ("fetch","stealthy-fetch"):
        cmd += ["--network-idle"]
    rc,so,se=run(cmd,120)
    text=path.read_text(errors="ignore") if path.exists() else ""
    return {"ok":rc==0 and len(text)>200,"path":str(path.relative_to(ROOT)),"text":text,"stdout":so,"stderr":se}

def links(html, base):
    vals=re.findall(r'href=[\"\']([^\"\']+)',html,re.I)
    out=[]
    for h in vals:
        u=urljoin(base,h)
        if urlparse(u).netloc==urlparse(base).netloc and u not in out: out.append(u)
    return out

def first_product_link(html,base):
    ls=links(html,base)
    pats=["/products/","/product/","/p/"]
    for p in pats:
        for u in ls:
            if p in u.lower(): return u
    return None

def textify(html):
    s=re.sub(r'<script\b[^>]*>.*?</script>',' ',html,flags=re.I|re.S)
    s=re.sub(r'<style\b[^>]*>.*?</style>',' ',s,flags=re.I|re.S)
    s=re.sub(r'<[^>]+>',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def assess(sig, html, product_html, meta):
    h=(html+" "+product_html).lower(); t=textify(html+" "+product_html)
    sid=sig["id"]
    if sid=="current_price": return ("A",PRICE_RE.findall(t)[:8]) if PRICE_RE.search(t) else ("C",[])
    if sid in ("reference_price","sale_price","discount_depth"):
        vals=PRICE_RE.findall(t); pct=PCT_RE.findall(t)
        return ("B",{"prices":vals[:10],"percentages":pct[:10]}) if len(vals)>=2 or pct else ("C",[])
    if sid=="product_url": return ("A",[meta.get("product_url")]) if meta.get("product_url") else ("C",[])
    if sid=="product_name":
        m=re.search(r'<h1\b[^>]*>(.*?)</h1>',product_html,re.I|re.S)
        return ("A",textify(m.group(1))[:300]) if m else ("C","")
    if sid=="product_images":
        imgs=re.findall(r'<img\b[^>]+(?:src|data-src)=[\"\']([^\"\']+)',product_html,re.I)
        return ("A",imgs[:10]) if imgs else ("C",[])
    if sid=="product_description": return ("B",textify(product_html)[:1000]) if product_html else ("D","")
    if sid in KEYWORDS:
        hits=[k for k in KEYWORDS[sid] if k in h]
        return ("B",hits) if hits else ("N/A",[])
    if sid=="rating":
        m=re.search(r'(?:rating|rated)[^0-9]{0,20}([0-5](?:\.\d)?)',t,re.I)
        return ("B",m.group(1)) if m else ("N/A","")
    if sid=="review_count":
        m=re.search(r'([\d,]+)\s+reviews?',t,re.I)
        return ("B",m.group(1)) if m else ("N/A","")
    if sid=="structured_json":
        ok=bool(re.search(r'application/ld\+json',html,re.I))
        return ("A",True) if ok else ("N/A",False)
    if sid=="sitemap":
        return ("B","tested separately")
    if sid=="shopify_json":
        shop=("cdn.shopify.com" in h or "shopify-section" in h or "myshopify" in h)
        return ("B",shop) if shop else ("N/A",False)
    if sid=="dynamic_js_content": return ("A",meta.get("dynamic_used",False)) if meta.get("dynamic_used") else ("N/A",False)
    if sid=="browser_only_content": return ("B",meta.get("dynamic_added_bytes",0)) if meta.get("dynamic_added_bytes",0)>500 else ("N/A",False)
    if sid=="anti_bot_response": return ("B",meta.get("static_blocked",False))
    if sid=="crawl_stability": return ("A",meta.get("repeat_ok",False)) if meta.get("repeat_ok") else ("C",False)
    if sid=="screenshot_capture": return ("C","not exercised in baseline runner")
    if sid=="xhr_fetch_data": return ("C","requires targeted browser instrumentation")
    if sid=="adaptive_selector_recovery": return ("C","requires controlled page-change test")
    if sid in ("proxy_requirement","session_requirement"): return ("C","not required unless failures persist")
    # generic presence probes
    terms={
      "variants":["variant","size","flavor","flavour","color","colour"],
      "product_identifier":["sku"],
      "category_collection_placement":["collection","category"],
      "product_count":["products"],
      "featured_products":["featured"],
      "homepage_hero_product":["hero"],
      "homepage_hero_image":["hero"],
      "homepage_hero_copy":["hero"],
      "homepage_promotional_blocks":["sale","save","offer"],
      "featured_collections":["featured collection"],
      "bestseller_blocks":["best seller","bestseller"],
      "promo_code":["code "],
      "pack_size":["pack","count"],
      "subscription_price":["subscribe"],
      "subscription_discount":["subscribe","save"],
      "variant_availability":["sold out","available"],
      "restock_state":["restock","notify me"],
      "review_widget_access":["yotpo","okendo","judge.me","reviews.io","stamped"],
      "new_product_presence":["new"],
      "removed_product_presence":[],
    }
    if sid in terms:
        hits=[x for x in terms[sid] if x in h]
        return ("B",hits) if hits else ("N/A",[])
    return ("C","not conclusively assessed by baseline automation")

rows=[]; site_profiles=[]
for s in sites:
    sid=s["id"]; url=s["url"]
    a=fetch(url,sid,"get")
    static_blocked=not a["ok"] or any(x in a["text"].lower() for x in ["access denied","captcha","cf-chl","just a moment"])
    b=None
    if static_blocked or len(a["text"])<5000:
        b=fetch(url,sid,"fetch")
    base_html=(b["text"] if b and b["ok"] and len(b["text"])>len(a["text"]) else a["text"])
    product_url=first_product_link(base_html,url)
    prod={"text":"","ok":False}
    if product_url:
        prod=fetch(product_url,sid+"-product","get")
        if not prod["ok"]:
            prod=fetch(product_url,sid+"-product","fetch")
    # repeat baseline homepage once
    time.sleep(1)
    rep=fetch(url,sid+"-repeat","get")
    meta={"product_url":product_url,"dynamic_used":bool(b and b["ok"]),"dynamic_added_bytes":(len(b["text"])-len(a["text"])) if b else 0,"static_blocked":static_blocked,"repeat_ok":a["ok"] and rep["ok"]}
    # sitemap direct
    sm=fetch(url.rstrip("/")+"/sitemap.xml",sid+"-sitemap","get")
    site_profiles.append({"site_id":sid,"name":s["name"],"url":url,"homepage_static_ok":a["ok"],"homepage_dynamic_ok":bool(b and b["ok"]),"static_bytes":len(a["text"]),"dynamic_bytes":len(b["text"]) if b else 0,"product_url":product_url,"product_ok":prod["ok"],"sitemap_ok":sm["ok"],"static_blocked":static_blocked})
    for sig in signals:
        if sig["id"]=="sitemap":
            outcome,val=("A",True) if sm["ok"] else ("D",False)
        else:
            outcome,val=assess(sig,base_html,prod["text"],meta)
        rows.append({"site_id":sid,"site":s["name"],"domain":urlparse(url).netloc,"signal_id":sig["id"],"signal":sig["label"],"group":sig["group"],"outcome":outcome,"value":val,"product_url":product_url,"collection_method":"Fetcher + DynamicFetcher fallback","evidence":a["path"],"notes":""})

(OUT/"site_profiles.json").write_text(json.dumps(site_profiles,indent=2))
(OUT/"results.json").write_text(json.dumps(rows,indent=2))

# combined markdown
site_ids=[x["id"] for x in sites]
by={(r["signal_id"],r["site_id"]):r for r in rows}
lines=["# Scrapling CCI Capability Benchmark — Baseline Run","","> Automated first-pass benchmark. C/D results identify where targeted site-specific testing is required; they are not final production verdicts.","","## Site Profiles",""]
for p in site_profiles:
    lines += [f"### {p['name']}",f"- URL: {p['url']}",f"- Static fetch: {'OK' if p['homepage_static_ok'] else 'FAIL'}",f"- Dynamic fallback: {'OK' if p['homepage_dynamic_ok'] else 'not used / failed'}",f"- Product page discovered: {p['product_url'] or 'No'}",f"- Sitemap: {'OK' if p['sitemap_ok'] else 'FAIL'}",f"- Static block suspected: {p['static_blocked']}",""]
lines += ["## Capability Matrix","","| Signal | "+ " | ".join([s["name"] for s in sites])+" |","|---|"+ "|".join(["---"]*len(sites))+"|"]
for sig in signals:
    lines.append("| "+sig["label"]+" | "+" | ".join(by[(sig["id"],x)]["outcome"] for x in site_ids)+" |")
from collections import Counter
cnt=Counter(r["outcome"] for r in rows)
lines += ["","## Automated outcome totals","",f"- A — Extracted cleanly: {cnt['A']}",f"- B — Extracted with custom/heuristic logic: {cnt['B']}",f"- C — Inconclusive/inconsistent: {cnt['C']}",f"- D — Unavailable in tested method: {cnt['D']}",f"- N/A — feature not observed: {cnt['N/A']}","","## Next Pass","","Any commercially important signal scored C or D should receive targeted site-specific testing using selectors, XHR capture, ShopifySpider where applicable, browser instrumentation, and repeatability checks before a production decision."]
(OUT/"benchmark.md").write_text("\n".join(lines))
print("\n".join(lines[:80]))
