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
    """Match provider IDs only via unique exact teams + start within 20 minutes.

    Reject ambiguous candidates, swapped home/away, missing start times, and
    games whose result timestamps cannot be tied to the forecast event.
    """
    games=completed.get("games",[])
    scored=[]
    # Freeze the earliest valid pregame prediction per event for unbiased scoring.
    earliest={}
    for row in ledger.get("forecasts",[]):
        event=row.get("event_id")
        stamp=timestamp(row.get("forecast_at"))
        if not event or not stamp:continue
        previous=earliest.get(event)
        if previous is None or stamp<timestamp(previous["forecast_at"]):earliest[event]=row
    for row in earliest.values():
        try:
            start=timestamp(row["event_start"])
            forecast_at=timestamp(row["forecast_at"])
            p=row["home_probability"]
            if not start or not forecast_at or not forecast_at<start or type(p) not in (int,float) or not math.isfinite(p) or not 0<p<1:continue
            candidates=[]
            for g in games:
                if g.get("home")!=row["home"] or g.get("away")!=row["away"]:continue
                game_start=timestamp(g.get("date"))
                if not game_start or abs((game_start-start).total_seconds())>1200:continue
                hs,aws=g.get("home_score"),g.get("away_score")
                if type(hs) not in (int,float) or type(aws) not in (int,float) or not math.isfinite(hs) or not math.isfinite(aws) or hs==aws:continue
                candidates.append(g)
            if len(candidates)!=1:continue
            g=candidates[0]
            y=int(g["home_score"]>g["away_score"])
            scored.append({"forecast_id":row["forecast_id"],"provider_event_id":str(g.get("event_id","")),"match_method":"exact_teams_unique_start_within_20m","home_probability":p,"home_won":y,"brier":round((p-y)**2,6)})
        except (KeyError,TypeError,ValueError):continue
    n=len(scored)
    mean_brier=sum(x["brier"] for x in scored)/n if n else None
    baseline=sum(x["home_won"] for x in scored)/n if n else None
    baseline_brier=sum((baseline-x["home_won"])**2 for x in scored)/n if n else None
    log_loss= -sum(x["home_won"]*math.log(x["home_probability"])+(1-x["home_won"])*math.log1p(-x["home_probability"]) for x in scored)/n if n else None
    buckets=[]
    for low,high in ((0,.2),(.2,.4),(.4,.6),(.6,.8),(.8,1.000001)):
        subset=[x for x in scored if low<=x["home_probability"]<high]
        if subset:buckets.append({"range":[low,min(high,1)],"count":len(subset),"mean_predicted":round(sum(x["home_probability"] for x in subset)/len(subset),6),"observed_home_win_rate":round(sum(x["home_won"] for x in subset)/len(subset),6)})
    return {"status":"research_only","matched_forecasts":len(scored),"metrics_sample_size":n,"log_loss":round(log_loss,6) if n else None,"empirical_home_rate_baseline_brier":round(baseline_brier,6) if n else None,"calibration_bins":buckets,"calibration_warning":"Small samples and in-sample baseline cannot establish predictive edge" if n<100 else "Compare with independent pregame bookmaker baselines before claiming edge",,"unique_events_in_ledger":len(earliest),"unmatched_events":len(earliest)-len(scored),"mean_brier":round(sum(x["brier"] for x in scored)/len(scored),6) if scored else None,"notes":"One earliest forecast per event; strict exact teams and unique start-time proximity; ambiguous or unverified results excluded","scored":scored}

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
            print(sport,"immutable forecasts added:",added,"strict cross-provider outcomes:",audit["matched_forecasts"])
if __name__=="__main__":main()
