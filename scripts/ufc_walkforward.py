#!/usr/bin/env python3
"""Leakage-safe UFC pre-fight probability evaluation. No fabricated probabilities."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path

def timestamp(value):
    if not isinstance(value,str):
        raise ValueError("Timestamp required")
    parsed=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timezone required")
    return parsed.astimezone(dt.timezone.utc)

def audit(predictions,results,min_settled=100):
    if not isinstance(predictions,list) or not isinstance(results,list):
        raise ValueError("Expected prediction and result arrays")
    outcomes={}
    for row in results:
        if not isinstance(row,dict):
            continue
        fid=row.get("fight_id")
        if not fid or fid in outcomes or row.get("winner") not in ("red","blue"):
            continue
        try: finished=timestamp(row["completed_at"])
        except (KeyError,ValueError,TypeError):continue
        outcomes[fid]=(row["winner"],finished)
    seen=set()
    settled=[]
    blocked=[]
    for row in predictions:
        if not isinstance(row,dict):
            continue
        fid=row.get("fight_id")
        if not fid or fid in seen:
            blocked.append({"fight_id":fid,"reason":"Duplicate or missing prediction identity"})
            continue
        seen.add(fid)
        try:
            generated=timestamp(row["generated_at"])
            start=timestamp(row["start_time"])
            p=row["red_win_probability"]
            if isinstance(p,bool) or not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<p<1:
                raise ValueError("Invalid probability")
            if generated>=start:
                raise ValueError("Prediction not pre-fight")
            if row.get("research_only") is not True or row.get("model_version") in (None,""):
                raise ValueError("Missing research-only model provenance")
            outcome=outcomes.get(fid)
            if outcome is None:
                raise ValueError("No verified settled result")
            winner,completed=outcome
            if completed<start:
                raise ValueError("Result predates fight")
            y=1 if winner=="red" else 0
            settled.append({"fight_id":fid,"p":p,"y":y,"brier":(p-y)**2,
                            "log_loss":-(y*math.log(p)+(1-y)*math.log1p(-p))})
        except (KeyError,ValueError,TypeError) as exc:
            blocked.append({"fight_id":fid,"reason":str(exc)})
    n=len(settled)
    brier=sum(x["brier"] for x in settled)/n if n else None
    log_loss=sum(x["log_loss"] for x in settled)/n if n else None
    base=sum(x["y"] for x in settled)/n if n else None
    base_brier=base*(1-base) if base is not None else None
    return {"sport":"UFC","schema":1,"graded":n,"blocked":blocked,
            "brier_score":brier,"log_loss":log_loss,"constant_base_rate_brier":base_brier,
            "calibration_status":"INSUFFICIENT_SAMPLE" if n<min_settled else "REQUIRES_INDEPENDENT_REVIEW",
            "bet_eligible":False,"roi":None,"hit_rate":None,
            "note":"Out-of-sample integrity and source verification require independent audit. No verified sportsbook prices."}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--predictions",required=True)
    parser.add_argument("--results",required=True)
    parser.add_argument("--output",default="backtests/reports/ufc_calibration.json")
    args=parser.parse_args()
    report=audit(json.loads(Path(args.predictions).read_text())["predictions"],
                 json.loads(Path(args.results).read_text())["results"])
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(f"UFC graded={report['graded']} calibration={report['calibration_status']}")

if __name__=="__main__":
    main()
