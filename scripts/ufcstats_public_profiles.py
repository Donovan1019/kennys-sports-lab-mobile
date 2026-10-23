#!/usr/bin/env python3
"""Bounded, fail-closed public UFCStats fighter-stat research adapter.

Only public fighter directory and matched fighter detail pages; no bypasses,
no authentication, no aggressive crawling. Respect robots/terms before enabling.
All outputs remain research-only and unverified for current fight readiness.
"""
import argparse
import datetime as dt
import json
import re
import time
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

BASE="http://ufcstats.com"
DIRECTORY=BASE+"/statistics/fighters?ftype=all"
USER_AGENT="KennysSportsLabResearch/1.0"
FIELDS={"SLpM":"sig_strikes_landed_per_min","SApM":"sig_strikes_absorbed_per_min",
        "Str. Acc.":"sig_strike_accuracy","Str. Def.":"sig_strike_defense",
        "TD Avg.":"takedowns_per_15","TD Acc.":"takedown_accuracy",
        "TD Def.":"takedown_defense","Sub. Avg.":"submission_attempts_per_15"}
class Page(HTMLParser):
 def __init__(self):
  super().__init__();self.links=[];self.text=[];self.href=None;self.linktext=[]
 def handle_starttag(self,tag,attrs):
  if tag=="a":
   self.href=dict(attrs).get("href");self.linktext=[]
 def handle_data(self,data):
  self.text.append(data)
  if self.href is not None:self.linktext.append(data)
 def handle_endtag(self,tag):
  if tag=="a" and self.href is not None:
   self.links.append((self.href," ".join(self.linktext).strip()))
   self.href=None
def key(s):
 return " ".join("".join(c for c in unicodedata.normalize("NFKD",s.casefold()) if not unicodedata.combining(c)).split())
def parse_directory(html):
 p=Page();p.feed(html)
 fighters={};grouped={}
 for href,name in p.links:
  if re.fullmatch(r"https?://ufcstats\.com/fighter-details/[0-9a-f]{32}",href or "") and name.strip():
   grouped.setdefault(href,[]).append(name.strip())
 for href,parts in grouped.items():
  # UFCStats commonly uses separate first-name and last-name links to one profile.
  for candidate in set(parts+[" ".join(parts[:2])]):
   fighters.setdefault(key(candidate),set()).add(href)
 return fighters
def parse_fighter(html):
 p=Page();p.feed(html)
 text=" ".join(" ".join(p.text).split())
 result={}
 for label,field in FIELDS.items():
  match=re.search(re.escape(label)+r"\s*:?\s*([0-9]+(?:\.[0-9]+)?%?)",text,re.I)
  if match:
   v=match.group(1);result[field]=float(v[:-1])/100 if v.endswith("%") else float(v)
 return result
def permitted(url,robots):
 if not url.startswith(BASE+"/"):return False
 path=urlparse(url).path
 if not (path.startswith("/fighter-details/") or path=="/statistics/fighters"):return False
 return robots.can_fetch(USER_AGENT,url)
def get(url,timeout=15):
 req=Request(url,headers={"User-Agent":USER_AGENT,"Accept":"text/html"})
 with urlopen(req,timeout=timeout) as res:
  final=res.geturl()
  if urlparse(final).hostname!="ufcstats.com":raise ValueError("Unexpected redirect")
  return res.read(2_000_000).decode("utf-8","replace")
def probe(card,fetch=get,robots=None,delay=1.5,max_fighters=32):
 names=sorted({f.get(side,"").strip() for f in card.get("fights",[]) for side in ("red","blue") if f.get(side)})
 if len(names)>max_fighters:raise ValueError("Card exceeds bounded fighter cap")
 if robots is None:
  robots=RobotFileParser();robots.set_url(BASE+"/robots.txt")
  try:robots.read()
  except Exception:return {"sport":"UFC","status":"ROBOTS_UNAVAILABLE","fighters":[],"bet_eligible":False}
 if not permitted(DIRECTORY,robots):
  return {"sport":"UFC","status":"ROBOTS_DISALLOW","fighters":[],"bet_eligible":False}
 try:directory=parse_directory(fetch(DIRECTORY))
 except Exception as e:return {"sport":"UFC","status":"DIRECTORY_UNAVAILABLE","error_type":type(e).__name__,"fighters":[],"bet_eligible":False}
 out=[]
 for name in names:
  matches=directory.get(key(name),set())
  if len(matches)!=1:
   out.append({"name":name,"status":"NOT_FOUND_OR_AMBIGUOUS","stats":None});continue
  url=next(iter(matches))
  if not permitted(url,robots):
   out.append({"name":name,"status":"ROBOTS_DISALLOW","stats":None});continue
  if delay:time.sleep(delay)
  try:
   stats=parse_fighter(fetch(url))
   status="PUBLIC_PROFILE_FOUND" if len(stats)==len(FIELDS) else "INCOMPLETE_PROFILE"
  except Exception:stats={};status="PROFILE_UNAVAILABLE"
  out.append({"name":name,"source_url":url,"status":status,"stats":stats,
              "observed_minutes":None,"stats_verified":False,"fighter_status_verified":False})
 return {"schema":1,"sport":"UFC","source":"UFCStats public fighter pages",
         "captured_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
         "status":"RESEARCH_ONLY","fighters":out,"bet_eligible":False,
         "limitations":["Site permission and uptime may vary","Public career rates are not current-form or matchup-adjusted",
                        "No verified observed minutes, fighter status, injury, weigh-in or bout length",
                        "Not a calibrated prediction or sportsbook feed"]}
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--card",default="feed/ufc_research.json")
 ap.add_argument("--output",default="feed/ufcstats_profiles.json")
 args=ap.parse_args()
 report=probe(json.loads(Path(args.card).read_text()))
 out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(report,indent=2)+"\n")
 print("UFCStats:",report["status"],"profiles:",len(report["fighters"]),"complete:",sum(x["status"]=="PUBLIC_PROFILE_FOUND" for x in report["fighters"]))
 from collections import Counter
 print("Profile statuses:",dict(Counter(x["status"] for x in report["fighters"])))
if __name__=="__main__":main()
