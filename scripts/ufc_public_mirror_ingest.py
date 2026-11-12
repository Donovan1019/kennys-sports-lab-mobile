#!/usr/bin/env python3
"""Free UFC fighter profiles from publicly published UFCStats CSV mirrors.

Source snapshots are descriptive career aggregates, NOT pre-fight training features.
Do not use for historical model backtesting without timestamped snapshots.
"""
import argparse,csv,io,json,datetime as dt,re,unicodedata
from pathlib import Path
from urllib.request import Request,urlopen
BASE="https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/"
FILES=("ufc_fighter_details.csv","ufc_fighter_tott.csv","ufc_fight_stats.csv")
def key(s):
 return " ".join(re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in unicodedata.normalize("NFKD",(s or "").casefold()) if not unicodedata.combining(c))).split())
def read_csv(name):
 if name not in FILES:raise ValueError("Unapproved source file")
 with urlopen(Request(BASE+name,headers={"User-Agent":"KennysSportsLabResearch/1.0"}),timeout=35) as f:
  data=f.read(18_000_000).decode("utf-8-sig")
 return list(csv.DictReader(io.StringIO(data)))
def pair(s):
 m=re.fullmatch(r"\s*(\d+)\s+of\s+(\d+)\s*",s or "")
 return (int(m.group(1)),int(m.group(2))) if m else (0,0)
def secs(s):
 m=re.fullmatch(r"(\d+):(\d{2})",s or "")
 return int(m.group(1))*60+int(m.group(2)) if m else 0
def build(card,details,tott,stats):
 profiles={}
 for row in details:
  name=" ".join(filter(None,[row.get("FIRST","").strip(),row.get("LAST","").strip()]))
  if name:
   profiles.setdefault(key(name),[]).append({"name":name,"url":row.get("URL"),"nickname":row.get("NICKNAME")})
 attrs={}
 for row in tott:
  if row.get("FIGHTER"):attrs.setdefault(key(row["FIGHTER"]),[]).append(row)
 totals={}
 for row in stats:
  name=key(row.get("FIGHTER",""))
  if not name:continue
  v=totals.setdefault(name,{"round_rows":0,"sig_landed":0,"sig_attempted":0,"total_landed":0,"td_landed":0,"td_attempted":0,"submission_attempts":0,"knockdowns":0,"control_seconds":0})
  if not any(pair(row.get(col)) != (0,0) for col in ("SIG.STR.","TD","TOTAL STR.")) and not secs(row.get("CTRL")):
   continue
  v["round_rows"]+=1
  for col,prefix in [("SIG.STR.","sig"),("TD","td"),("TOTAL STR.","total")]:
   made,attempted=pair(row.get(col))
   v[prefix+"_landed"]+=made
   if prefix!="total":v[prefix+"_attempted"]+=attempted
  for col,dest in [("SUB.ATT","submission_attempts"),("KD","knockdowns")]:
   try:v[dest]+=int(row.get(col) or 0)
   except ValueError:pass
  v["control_seconds"]+=secs(row.get("CTRL"))
 names=sorted({f.get(side,"").strip() for f in card.get("fights",[]) for side in ("red","blue") if f.get(side)})
 output=[]
 for name in names:
  ident=profiles.get(key(name),[])
  attr=attrs.get(key(name),[])
  stat=totals.get(key(name))
  unique=len(ident)==1 and len(attr)==1
  output.append({"name":name,"status":"MATCHED_HISTORICAL_STATS" if unique and stat and stat["round_rows"]>=1 else "INSUFFICIENT_OR_AMBIGUOUS",
                 "source_profile":ident[0]["url"] if unique else None,
                 "height":attr[0].get("HEIGHT") if unique else None,
                 "weight":attr[0].get("WEIGHT") if unique else None,
                 "reach":attr[0].get("REACH") if unique else None,
                 "stance":attr[0].get("STANCE") if unique else None,
                 "career_round_totals":stat if unique else None,
                 "fighter_status_verified":False,"stats_asof_verified":False,"bet_eligible":False})
 return {"schema":1,"sport":"UFC","source":"Greco1899/scrape_ufc_stats public CSV mirror","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat(),
         "source_files":list(FILES),"fighters":output,"bet_eligible":False,"research_only":True,
         "limitations":["Historical snapshot is not point-in-time safe for backtesting","Round rows are not full five-minute exposure denominators","No verified current fighter availability or sportsbook prices"]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--card",default="feed/ufc_research.json");ap.add_argument("--output",default="feed/ufc_fighter_stats_mirror.json")
 a=ap.parse_args();card=json.loads(Path(a.card).read_text())
 result=build(card,*(read_csv(x) for x in FILES))
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n")
 print("Fighter rows:",len(result["fighters"]),"matched:",sum(x["status"]=="MATCHED_HISTORICAL_STATS" for x in result["fighters"]))
if __name__=="__main__":main()
