"""Immutable pregame forecast ledger and chronological outcome scoring.

Only forecasts recorded before a game's verified start may enter outcome
scoring. No historical forecasts are reconstructed after results are known.
"""
import json
import math
from pathlib import Path
from datetime import datetime,timezone

def timestamp(value):
    try:
        d=datetime.fromisoformat(value.replace("Z","+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError,TypeError,AttributeError):return None

def record(ledger,forecasts,odds,now):
    if now.tzinfo is None:raise ValueError("Timezone-aware clock required")
    by_id={}
    for row in odds.get("odds",[]):
        if row.get("event_id") and row.get("commence_time"):
            start=timestamp(row["commence_time"])
            if start:by_id[row["event_id"]]=start
    entries={r["forecast_id"]:r for r in ledger.get("forecasts",[]) if r.get("forecast_id")}
    added=0
    for row in forecasts.get("events",[]):
        p=row.get("model_probability")
        event=row.get("event_id")
        asof=timestamp(row.get("asof"))
        start=by_id.get(event)
        if type(p) not in (float,int) or not math.isfinite(p) or not 0<p<1 or not asof or not start or asof>now or not asof<start:continue
        key=f"{event}|{asof.isoformat()}"
        if key in entries:continue
        entries[key]={"forecast_id":key,"event_id":event,"away":row["away"],"home":row["home"],"forecast_at":asof.isoformat(),"event_start":start.isoformat(),"home_probability":p,"status":"experimental_research_only"}
        added+=1
    return {"status":"immutable_research_ledger","forecasts":sorted(entries.values(),key=lambda r:r["forecast_id"]),"added":added}

def score(ledger,completed):
    by_id={str(g.get("event_id")):g for g in completed.get("games",[]) if g.get("event_id")}
    scored=[]
    for row in ledger.get("forecasts",[]):
        g=by_id.get(str(row.get("event_id")))
        if not g:continue
        # The ESPN event ID may differ from the sportsbook event ID. Never
        # match by approximate team name or retrospectively guess outcomes.
        try:
            if g["home"]!=row["home"] or g["away"]!=row["away"]:continue
            if type(g["home_score"]) not in (int,float) or type(g["away_score"]) not in (int,float):continue
            p=row["home_probability"]
            if not 0<p<1 or not timestamp(row["forecast_at"])<timestamp(row["event_start"]):continue
            y=int(g["home_score"]>g["away_score"])
            scored.append({"forecast_id":row["forecast_id"],"home_probability":p,"home_won":y,"brier":round((p-y)**2,6)})
        except (KeyError,TypeError,ValueError):continue
    return {"status":"research_only","matched_forecasts":len(scored),"mean_brier":round(sum(x["brier"] for x in scored)/len(scored),6) if scored else None,"notes":"Only exact event IDs and team names are scored; missing cross-provider IDs remain unmatched","scored":scored}

def main():
    now=datetime.now(timezone.utc)
    for sport,completed in (("basketball_nba","nba"),("icehockey_nhl","nhl")):
        forecast_path=Path(f"feed/{sport}_pregame_research.json")
        odds_path=Path(f"feed/{sport}.json")
        if not forecast_path.exists() or not odds_path.exists():continue
        ledger_path=Path(f"feed/{sport}_forecast_ledger.json")
        old=json.loads(ledger_path.read_text()) if ledger_path.exists() else {"forecasts":[]}
        result=record(old,json.loads(forecast_path.read_text()),json.loads(odds_path.read_text()),now)
        added=result.pop("added")
        if added:ledger_path.write_text(json.dumps(result,indent=2)+"\n")
        completed_path=Path(f"feed/{completed}_completed_games.json")
        if completed_path.exists():
            audit=score(result,json.loads(completed_path.read_text()))
            Path(f"feed/{sport}_forecast_outcomes.json").write_text(json.dumps(audit,indent=2)+"\n")
            print(sport,"immutable forecasts added:",added,"exact-ID outcomes:",audit["matched_forecasts"])
if __name__=="__main__":main()
