#!/usr/bin/env python3
"""Fetch verified ESPN NBA team box-score stats for historical completed games.
Missing data stays missing. Rate limited; no estimates.
"""
import datetime as dt
import json
import pathlib
import time
import urllib.request

ROOT=pathlib.Path("data")
HISTORY=ROOT/"nba_ml_historical_games.json"
OUTPUT=ROOT/"nba_ml_possession_boxscores.json"
URL="https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
STAT_ALIASES={"fieldGoalsAttempted":"fga","freeThrowsAttempted":"fta","offensiveRebounds":"orb","turnovers":"turnovers"}
def extract(summary,game):
    box=summary.get("boxscore",{}).get("players",[])
    result={}
    for side in box:
        name=side.get("team",{}).get("displayName")
        if name not in (game["home"],game["away"]):continue
        totals={}
        for statgroup in side.get("statistics",[]):
            labels=statgroup.get("labels",[])
            # ESPN totals are supplied as final row; verify labels and numeric fields.
            athletes=statgroup.get("athletes",[])
            if not athletes:continue
            total=next((x for x in athletes if x.get("athlete",{}).get("displayName")=="TEAM"),None)
            if total is None:continue
            for label,value in zip(labels,total.get("stats",[])):
                totals[label]=value
        result[name]=totals
    # Prefer official team statistics, not summed player entries or inferred possessions.
    competitors=summary.get("header",{}).get("competitions",[{}])[0].get("competitors",[])
    for c in competitors:
        name=c.get("team",{}).get("displayName")
        if name not in (game["home"],game["away"]):continue
        stats={}
        for x in c.get("statistics",[]):
            key=x.get("name")
            if key in STAT_ALIASES:
                try:stats[STAT_ALIASES[key]]=float(x.get("displayValue",x.get("value")))
                except (TypeError,ValueError):pass
        try:stats["points"]=float(c["score"])
        except (KeyError,ValueError,TypeError):pass
        if len(stats)==5:result[name]=stats
    if len(result)!=2 or any(not all(k in result[t] for k in ("fga","fta","orb","turnovers","points")) for t in (game["home"],game["away"])):
        return None
    return {"id":str(game["id"]),"date":game["date"],"home":game["home"],"away":game["away"],"box":result}

def main():
    history=json.loads(HISTORY.read_text())
    games=sorted((g for day in history.get("days",{}).values() for g in day),key=lambda g:g["date"],reverse=True)
    try: existing=json.loads(OUTPUT.read_text())
    except (OSError,ValueError):existing={}
    cached={str(g["id"]):g for g in existing.get("games",[]) if "box" in g}
    attempts=0;added=0
    for g in games:
        if str(g["id"]) in cached or attempts>=80:continue
        attempts+=1
        try:
            req=urllib.request.Request(URL.format(event_id=g["id"]),headers={"User-Agent":"KSL-NBA-Boxscore/1.0"})
            with urllib.request.urlopen(req,timeout=12) as response:summary=json.load(response)
            row=extract(summary,g)
            if row:cached[str(g["id"])]=row;added+=1
        except (OSError,ValueError,KeyError,TimeoutError):pass
        time.sleep(.2)
    OUTPUT.write_text(json.dumps({"source":"ESPN NBA summary box scores","games":list(cached.values()),"fetched_at":dt.datetime.now(dt.timezone.utc).isoformat()},indent=2)+"\n")
    print("NBA box-score evidence:",len(cached),"total",added,"added",attempts,"attempted")
if __name__=="__main__":main()
