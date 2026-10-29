#!/usr/bin/env python3
"""Fail-closed NBA ML prediction feed builder. No sportsbook odds as predictive inputs."""
import argparse, datetime as dt, json, math, pathlib
from zoneinfo import ZoneInfo

def build(odds, ratings, now):
    if ratings.get("status") != "validated" or ratings.get("calibration_passed") is not True:
        raise ValueError("Independent team ratings have not passed calibration")
    if not ratings.get("training_cutoff") or not ratings.get("validation_report"):
        raise ValueError("Missing training cutoff or validation report")
    cutoff=dt.datetime.fromisoformat(ratings["training_cutoff"].replace("Z","+00:00"))
    if cutoff.tzinfo is None or cutoff>now: raise ValueError("Invalid training cutoff")
    if (now-cutoff).total_seconds()>14*86400: raise ValueError("Team ratings older than 14 days")
    if ratings.get("season") is None: raise ValueError("Missing season")
    teams=ratings.get("teams",{})
    if not isinstance(teams,dict) or len(teams)<28: raise ValueError("Insufficient independent team ratings")
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in teams.values()):
        raise ValueError("Invalid team rating")
    if odds.get("status")!="ok" or odds.get("sport")!="basketball_nba":raise ValueError("Invalid odds snapshot")
    seen=set(); predictions=[]
    for row in odds.get("odds",[]):
        if row.get("market")!="h2h":continue
        eid=row.get("event_id"); event=row.get("event","")
        if not eid or eid in seen or " @ " not in event:continue
        seen.add(eid)
        away,home=event.split(" @ ",1)
        if away not in teams or home not in teams:continue
        tip=dt.datetime.fromisoformat(row["commence_time"].replace("Z","+00:00"))
        if tip<=now:continue
        if cutoff>=tip: raise ValueError("Training cutoff overlaps a forecast event")
        date=tip.astimezone(ZoneInfo("America/New_York")).date().isoformat()
        # Ratings must be derived from historical results, not bookmaker prices.
        difference=float(teams[home])-float(teams[away])+float(ratings.get("home_advantage",0))
        scale=float(ratings.get("logistic_scale",1))
        if not math.isfinite(scale) or scale<=0:raise ValueError("Invalid logistic scale")
        p=1/(1+math.exp(-max(-30,min(30,difference/scale))))
        for team,prob in ((home,p),(away,1-p)):
            predictions.append({"event_id":eid,"team":team,"date_et":date,"win_probability":round(prob,6)})
    return {"status":"validated","sport":"basketball_nba","generated_at":now.isoformat(),"calibration_passed":True,"model_version":ratings.get("model_version","unversioned"),"validation_report":ratings["validation_report"],"training_cutoff":ratings["training_cutoff"],"predictions":predictions}

def main():
    p=argparse.ArgumentParser();p.add_argument("--odds",default="feed/basketball_nba.json");p.add_argument("--ratings",default="data/nba_ml_validated_ratings.json");p.add_argument("--output",default="feed/nba_ml_predictions.json");args=p.parse_args()
    output=pathlib.Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    now=dt.datetime.now(dt.timezone.utc)
    try:
        result=build(json.loads(pathlib.Path(args.odds).read_text()),json.loads(pathlib.Path(args.ratings).read_text()),now)
        if not result["predictions"]:raise ValueError("No eligible events")
    except (OSError,ValueError,KeyError,TypeError,OverflowError) as exc:
        result={"status":"unavailable","sport":"basketball_nba","generated_at":now.isoformat(),"calibration_passed":False,"predictions":[],"reason":str(exc)[:200]}
    output.write_text(json.dumps(result,indent=2)+"\n")
    print("NBA ML prediction feed:",result["status"],len(result["predictions"]))
if __name__=="__main__":main()
