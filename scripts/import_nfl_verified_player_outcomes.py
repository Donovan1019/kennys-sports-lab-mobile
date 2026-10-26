#!/usr/bin/env python3
"""Independent ESPN final-box-score importer. Fail closed on ambiguous event/player matches."""
import json, urllib.request, urllib.parse
from datetime import datetime,timezone,timedelta
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parent.parent
LEDGER=ROOT/"feed/nfl_prop_forecast_ledger.json"
OUTPUT=ROOT/"feed/nfl_prop_verified_outcomes.json"
MARKETS={"player_pass_yds":"passingYards","player_pass_tds":"passingTouchdowns","player_rush_yds":"rushingYards","player_reception_yds":"receivingYards","player_receptions":"receptions"}
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"KennysSportsLab/1.0"})
    with urllib.request.urlopen(req,timeout=25) as f:return json.load(f)
def player_stats(summary):
    result=defaultdict(list)
    for team in summary.get("boxscore",{}).get("players",[]):
        for group in team.get("statistics",[]):
            labels=group.get("labels",[])
            for row in group.get("athletes",[]):
                name=row.get("athlete",{}).get("displayName")
                values=row.get("stats",[])
                if not name or len(values)!=len(labels):continue
                result[name.lower()].append(dict(zip(labels,values)))
    return result
def parse_stat(rows,market):
    # ESPN stat labels can vary; use category indexes, never infer from unrelated categories.
    specs={"player_pass_yds":("passing","YDS"),"player_pass_tds":("passing","TD"),"player_rush_yds":("rushing","YDS"),"player_reception_yds":("receiving","YDS"),"player_receptions":("receiving","REC")}
    # Caller supplies grouped rows with category explicitly.
    category,label=specs[market]
    vals=[]
    for row in rows:
        if row["category"]!=category:continue
        try:vals.append(float(row["values"][label]))
        except (ValueError,TypeError,KeyError):pass
    return vals[0] if len(vals)==1 else None
def extract(summary):
    result=defaultdict(list)
    for team in summary.get("boxscore",{}).get("players",[]):
        for group in team.get("statistics",[]):
            category=group.get("name","").lower()
            if category not in ("passing","rushing","receiving"):continue
            labels=group.get("labels",[])
            for row in group.get("athletes",[]):
                name=row.get("athlete",{}).get("displayName")
                values=row.get("stats",[])
                if name and len(values)==len(labels):
                    result[name.lower()].append({"category":category,"values":dict(zip(labels,values))})
    return result
def main():
    forecasts=json.loads(LEDGER.read_text())["forecasts"]
    old=json.loads(OUTPUT.read_text()) if OUTPUT.exists() else []
    if not isinstance(old,list):raise ValueError("Existing verified outcome archive malformed")
    prior={(x["event_id"],x["player"],x["market"]):x for x in old}
    pending=[f for f in forecasts if f["market"] in MARKETS and (f["event_id"],f["player"],f["market"]) not in prior and datetime.fromisoformat(f["kickoff"].replace("Z","+00:00"))<datetime.now(timezone.utc)-timedelta(hours=4)]
    byday=defaultdict(list)
    for f in pending:byday[f["kickoff"][:10].replace("-","")].append(f)
    added=0;unmatched=0;summary_cache={}
    for day,group in byday.items():
        try:board=get("https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates="+day)
        except Exception as exc:print("Scoreboard unavailable",day,type(exc).__name__);continue
        finals=[]
        for e in board.get("events",[]):
            c=(e.get("competitions") or [{}])[0]
            if not (e.get("status",{}).get("type",{}).get("completed") or c.get("status",{}).get("type",{}).get("completed")):continue
            try:dt=datetime.fromisoformat(e["date"].replace("Z","+00:00"))
            except (ValueError,KeyError):continue
            finals.append((e,dt))
        for f in group:
            kick=datetime.fromisoformat(f["kickoff"].replace("Z","+00:00"))
            matches=[e for e,dt in finals if abs((dt-kick).total_seconds())<=1200]
            if f.get("event"):
                expected={x.strip().lower() for x in f["event"].split(" @ ")}
                matches=[e for e in matches if {x.get("team",{}).get("displayName","").lower() for x in e["competitions"][0].get("competitors",[])}==expected]
            # Without exact teams, concurrent kickoffs are ambiguous: never guess.
            if len(matches)>1 and not f.get("event"):
                possible=[]
                for candidate in matches:
                    cid=str(candidate["id"])
                    if cid not in summary_cache:
                        try:summary_cache[cid]=extract(get("https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="+urllib.parse.quote(cid)))
                        except Exception:summary_cache[cid]={}
                    if f["player"].lower() in summary_cache[cid]:possible.append(candidate)
                matches=possible
            if len(matches)!=1:unmatched+=1;continue
            e=matches[0];key=(f["event_id"],f["player"],f["market"])
            if key in prior:continue
            cid=str(e["id"])
            if cid not in summary_cache:
                try:summary_cache[cid]=extract(get("https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="+urllib.parse.quote(cid)))
                except Exception:summary_cache[cid]={}
            stats=summary_cache[cid]
            value=parse_stat(stats.get(f["player"].lower(),[]),f["market"])
            if value is None:unmatched+=1;continue
            row={"event_id":f["event_id"],"player":f["player"],"market":f["market"],"outcome":value,"verified_at":datetime.now(timezone.utc).isoformat(),"source":"https://www.espn.com/nfl/game/_/gameId/"+str(e["id"])}
            prior[key]=row;added+=1
    if added:OUTPUT.write_text(json.dumps(list(prior.values()),indent=2)+"\n")
    print(json.dumps({"newly_verified":added,"total_verified":len(prior),"ambiguous_or_missing":unmatched,"pending":len(pending)}))
if __name__=="__main__":main()
