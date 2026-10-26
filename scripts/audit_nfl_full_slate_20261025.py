#!/usr/bin/env python3
"""Audit actual completed NFL slate against immutable pregame forecasts.

Does not invent historical predictions. Uses ESPN final scoreboard for schedule
and only counts saved forecasts created before each event's kickoff.
"""
import json, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent.parent
DATE="20261025"
def utc(s): return datetime.fromisoformat(s.replace("Z","+00:00"))
def main():
    url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates="+DATE
    req=urllib.request.Request(url,headers={"User-Agent":"KennysSportsLab/1.0"})
    with urllib.request.urlopen(req,timeout=30) as response: board=json.load(response)
    ledger=json.loads((ROOT/"feed/nfl_prop_forecast_ledger.json").read_text()).get("forecasts",[])
    graded=json.loads((ROOT/"feed/nfl_prop_graded_snapshots.json").read_text())
    games=[]
    for e in board.get("events",[]):
        c=(e.get("competitions") or [{}])[0]
        if not (e.get("status",{}).get("type",{}).get("completed") or c.get("status",{}).get("type",{}).get("completed")): continue
        if utc(e["date"]).astimezone(ZoneInfo("America/New_York")).date().isoformat()!="2026-10-25":continue
        teams={x.get("homeAway"):x.get("team",{}).get("displayName","") for x in c.get("competitors",[])}
        scores={x.get("homeAway"):int(x["score"]) if str(x.get("score","")).isdigit() else None for x in c.get("competitors",[])}
        name=teams.get("away","")+" @ "+teams.get("home","")
        kickoff=e.get("date")
        # Event IDs differ between Odds API and ESPN. Require both event team
        # names and kickoff proximity when the source supplies event identity.
        def same(f):
            if f.get("event")!=name and f.get("event_id") not in {g.get("event_id") for g in graded if g.get("espn_event_id")==str(e["id"]) and g.get("outcome_verified") is True}:return False
            try:return abs((utc(f["kickoff"])-utc(kickoff)).total_seconds())<=1200
            except (ValueError,KeyError,TypeError):return False
        saved=[f for f in ledger if same(f) and f.get("forecast_at") and utc(f["forecast_at"])<utc(kickoff) and f.get("quoted_at") and utc(f["quoted_at"])<utc(kickoff)]
        verified=[f for f in graded if f.get("espn_event_id")==str(e["id"]) and f.get("outcome_verified") is True]
        unique={(f.get("player"),f.get("market"),f.get("line"),f.get("bookmaker")) for f in saved}
        winner="TIE" if scores.get("away")==scores.get("home") else teams.get("away") if scores.get("away") is not None and scores.get("home") is not None and scores["away"]>scores["home"] else teams.get("home") if scores.get("away") is not None and scores.get("home") is not None else None
        games.append({"away_score":scores.get("away"),"home_score":scores.get("home"),"winner":winner,"final_score_verified":scores.get("away") is not None and scores.get("home") is not None,"espn_event_id":str(e["id"]),"game":name,"kickoff":kickoff,"archived_pregame_quotes":len(saved),"unique_archived_props":len(unique),"verified_grades":len(verified),"status":"GRADED" if verified else "SAVED_AWAITING_GRADING" if saved else "NO_ARCHIVED_PREGAME_FORECAST"})
    result={"date":"2026-10-25","games":games,"completed_games":len(games),"games_with_pregame_forecasts":sum(x["archived_pregame_quotes"]>0 for x in games),"games_with_verified_grades":sum(x["verified_grades"]>0 for x in games),"note":"Final scores and winners are official game results, not model prediction grades. Missing pregame predictions cannot be counted as live-model grades. Historical backtests must be separate."}
    out=ROOT/"feed/nfl_full_slate_20261025_audit.json"
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="games"}))
if __name__=="__main__":main()
