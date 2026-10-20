"""Conservative prediction publication gate.

Only independently evaluated game-level forecasts can be published.
Market-implied probabilities and historical bootstraps do NOT qualify.
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

MIN_TRIALS=10000
def parse_time(value):
    if not isinstance(value,str): raise ValueError("Missing timestamp")
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None: raise ValueError("Timestamp must include timezone")
    return dt.astimezone(timezone.utc)

def validate_prediction(p, odds_rows):
    required=("sport","event_id","market","selection","model_version","input_timestamp",
              "model_probability","simulations","status","is_forecast","backtest")
    if any(k not in p for k in required): raise ValueError("Missing required forecast metadata")
    if p["status"]!="validated" or p["is_forecast"] is not True:
        raise ValueError("Unvalidated prediction")
    if p["market"] not in ("h2h","spreads","totals"): raise ValueError("Unknown market")
    prob=p["model_probability"]
    if isinstance(prob,bool) or not isinstance(prob,(float,int)) or not math.isfinite(prob) or not 0<prob<1:
        raise ValueError("Invalid probability")
    if type(p["simulations"]) is not int or p["simulations"]<MIN_TRIALS:
        raise ValueError("Insufficient simulation trials")
    if not isinstance(p["model_version"],str) or not p["model_version"].strip():
        raise ValueError("Missing model version")
    ts=parse_time(p["input_timestamp"])
    if ts>datetime.now(timezone.utc): raise ValueError("Future input timestamp")
    backtest=p["backtest"]
    if not isinstance(backtest,dict) or backtest.get("method")!="walk_forward" or backtest.get("passed") is not True:
        raise ValueError("Independent walk-forward validation required")
    if not isinstance(backtest.get("sample_size"),int) or backtest["sample_size"]<100:
        raise ValueError("Insufficient backtest sample")
    if not isinstance(backtest.get("brier"),(int,float)) or not 0<=backtest["brier"]<=1:
        raise ValueError("Missing calibration metric")
    if not isinstance(p["sport"],str) or not isinstance(p["event_id"],str) or not isinstance(p["selection"],str):
        raise ValueError("Invalid event identity")
    matches=[r for r in odds_rows if r.get("sport")==p["sport"] and r.get("event_id")==p["event_id"]
             and r.get("market")==p["market"] and r.get("selection")==p["selection"]
             and r.get("point")==p.get("point")]
    if not matches:raise ValueError("Forecast has no exact sportsbook market match")
    return True

def publish(candidates, odds_rows, output):
    accepted=[]
    errors=[]
    for index,p in enumerate(candidates):
        try:
            validate_prediction(p,odds_rows)
            accepted.append(p)
        except (ValueError,TypeError,KeyError) as exc:
            errors.append({"index":index,"error":str(exc)})
    doc={"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),
         "description":"Independent validated game forecasts only; market odds are not model forecasts.",
         "predictions":accepted,"rejected_count":len(errors),"rejection_reasons":errors[:25]}
    Path(output).write_text(json.dumps(doc,indent=2)+"\n")
    return doc

if __name__=="__main__":
    odds=[]
    for file in Path("feed").glob("*.json"):
        try:
            data=json.loads(file.read_text())
            if data.get("source")=="the-odds-api-v4":
                for row in data.get("odds",[]):odds.append({**row,"sport":data.get("sport")})
        except (ValueError,OSError):continue
    candidate_path=Path("feed/model_candidates.json")
    candidates=json.loads(candidate_path.read_text()).get("predictions",[]) if candidate_path.exists() else []
    result=publish(candidates,odds,"feed/model_predictions.json")
    print("Validated forecasts:",len(result["predictions"]),"Rejected:",result["rejected_count"])
