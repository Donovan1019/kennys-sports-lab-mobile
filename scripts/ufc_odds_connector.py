#!/usr/bin/env python3
"""Provider-neutral UFC moneyline quote ingestion (no scraping or paid APIs).

Accept a local authorized JSON export with source/timestamp and optional
independently validated model forecasts. Fail closed on any ambiguity.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
from scripts.ufc_market_ev import assess

def parse_time(s):
    x=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
    if x.utcoffset() is None:
        raise ValueError("Timezone required")
    return x

def normalize(snapshot):
    if snapshot.get("schema")!=1 or snapshot.get("sport")!="UFC":
        raise ValueError("Unexpected quote snapshot schema")
    if snapshot.get("source_authorized") is not True:
        raise ValueError("Quote source not authorized")
    observed=parse_time(snapshot["captured_at_utc"])
    output=[]
    seen=set()
    for row in snapshot.get("moneylines",[]):
        if not isinstance(row,dict):
            continue
        required=("event_id","fighter","opponent","fighter_odds","opponent_odds",
                  "event_start_utc","sportsbook")
        if any(k not in row for k in required):
            output.append({"eligible":False,"reason":"MISSING_QUOTE_FIELDS"})
            continue
        try:
            event=parse_time(row["event_start_utc"])
            if observed>=event:
                raise ValueError("Stale or post-event capture")
            key=(row["event_id"],row["sportsbook"],tuple(sorted((row["fighter"],row["opponent"]))))
            if key in seen:
                raise ValueError("Duplicate market")
            seen.add(key)
            # No model probability is assumed from the market price.
            p=row.get("model_probability")
            if p is None:
                output.append({"eligible":False,"reason":"MISSING_INDEPENDENT_MODEL_PROBABILITY",
                               "event_id":row["event_id"],"sportsbook":row["sportsbook"]})
                continue
            q={**row,"observed_at_utc":snapshot["captured_at_utc"],
               "model_calibrated":row.get("model_calibrated") is True,
               "fighters_verified":row.get("fighters_verified") is True,
               "source_verified":snapshot["source_authorized"] is True and row.get("source_verified") is True,
               "odds_executable":row.get("odds_executable") is True}
            output.append(assess(q))
        except (ValueError,TypeError,KeyError,AttributeError) as exc:
            output.append({"eligible":False,"reason":"INVALID_QUOTE","detail":str(exc)})
    return {"schema":1,"sport":"UFC","source":snapshot.get("source"),
            "captured_at_utc":snapshot["captured_at_utc"],"markets":output,
            "bet_eligible":False,"research_only":True,
            "note":"An authorized quote import is not proof of a calibrated or executable betting edge."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    result=normalize(json.loads(Path(args.input).read_text()))
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("Imported markets:",len(result["markets"]))
    print("Candidate flags:",sum(bool(x.get("eligible")) for x in result["markets"]))
    print("Research only:",result["research_only"])

if __name__=="__main__":
    main()
