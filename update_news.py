#!/usr/bin/env python3
"""Collect recent publisher RSS/Atom headlines into news.json."""
import datetime as dt
import email.utils
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SOURCES = [
 ("The Verge","https://www.theverge.com/rss/index.xml","other"),
 ("Ars Technica","https://feeds.arstechnica.com/arstechnica/index","other"),
 ("TechCrunch","https://techcrunch.com/feed/","other"),
 ("9to5Mac","https://9to5mac.com/feed/","apple"),
 ("MacRumors","https://www.macrumors.com/macrumors.xml","apple"),
 ("9to5Google","https://9to5google.com/feed/","google"),
 ("Google Blog","https://blog.google/rss/","google"),
 ("YouTube Official Blog","https://blog.youtube/feed/","youtube"),
 ("Microsoft Blog","https://blogs.microsoft.com/feed/","other"),
]
def clean(s):
 return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",s or ""))).strip()
def published(s):
 try:
  x=email.utils.parsedate_to_datetime(s)
 except (ValueError,TypeError):
  try:x=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
  except (ValueError,TypeError):return None
 if x.tzinfo is None:x=x.replace(tzinfo=dt.timezone.utc)
 return x.astimezone(dt.timezone.utc)
def category(title,summary,default):
 # Match YouTube in the headline, not incidental text in the description.
 t=title.lower()
 if re.search(r"\byou\s*tube\b|\byoutubers?\b",t) or default=="youtube":return "youtube"
 if any(w in t for w in ("artificial intelligence","chatgpt","gemini","copilot","openai")):return "ai"
 if any(w in t for w in ("apple","iphone","ipad","macbook")):return "apple"
 if any(w in t for w in ("google","android","pixel")):return "google"
 return default
def fetch(source):
 name,feed,default=source
 try:
  req=urllib.request.Request(feed,headers={"User-Agent":"TechToday/1.0 RSS reader","Accept":"application/rss+xml,application/atom+xml,application/xml"})
  with urllib.request.urlopen(req,timeout=15) as response:root=ET.fromstring(response.read(4000000))
 except Exception as exc:
  print("WARN",name,exc);return []
 items=root.findall(".//item") or root.findall("{http://www.w3.org/2005/Atom}entry")
 results=[]
 for item in items[:45]:
  def get(*tags):
   for tag in tags:
    node=item.find(tag)
    if node is not None and node.text:return node.text.strip()
   return ""
  title=clean(get("title","{http://www.w3.org/2005/Atom}title"))
  link=get("link")
  if not link:
   for node in item.findall("{http://www.w3.org/2005/Atom}link"):
    if node.attrib.get("rel","alternate")=="alternate":link=node.attrib.get("href","");break
  summary=clean(get("description","{http://www.w3.org/2005/Atom}summary"))[:260]
  date=published(get("pubDate","{http://www.w3.org/2005/Atom}published","{http://www.w3.org/2005/Atom}updated"))
  if not title or not link.startswith("https://") or date is None:continue
  age=(dt.datetime.now(dt.timezone.utc)-date).total_seconds()
  if age<0 or age>=21*86400:continue
  image=""
  for node in item.iter():
   if node.tag.endswith(("thumbnail","enclosure","content")):
    candidate=node.attrib.get("url","")
    if candidate.startswith("https://") and (node.tag.endswith("thumbnail") or "image" in node.attrib.get("type","")):image=candidate;break
  results.append(dict(title=title,url=link,source=name,published=date.isoformat(),summary=summary,image=image,category=category(title,summary,default)))
 return results
def main():
 path=Path(__file__).with_name("news.json")
 old=json.loads(path.read_text()) if path.exists() else {"articles":[]}
 articles=[]
 with ThreadPoolExecutor(max_workers=6) as pool:
  for future in as_completed([pool.submit(fetch,s) for s in SOURCES]):articles.extend(future.result())
 # Correct categories on previously collected articles too.
 for a in old.get("articles",[]):
  default=next((s[2] for s in SOURCES if s[0]==a.get("source")),"other")
  a["category"]=category(a.get("title",""),a.get("summary",""),default)
  articles.append(a)
 dedup={}
 for article in articles:
  key=re.sub(r"[^a-z0-9]","",article["title"].lower())[:110]
  if key and (key not in dedup or len(article.get("summary",""))>len(dedup[key].get("summary",""))):dedup[key]=article
 now=dt.datetime.now(dt.timezone.utc)
 recent=[a for a in dedup.values() if a.get("published") and 0<=(now-dt.datetime.fromisoformat(a["published"])).total_seconds()<21*86400]
 recent.sort(key=lambda a:a["published"],reverse=True)
 if not recent and old.get("articles"):return
 path.write_text(json.dumps({"updated_at":now.isoformat(),"articles":recent[:160]},indent=2,ensure_ascii=False)+"\n")
 print("Collected",len(recent[:160]),"articles")
if __name__=="__main__":main()
