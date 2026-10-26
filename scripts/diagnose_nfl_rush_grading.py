#!/usr/bin/env python3
"""Identify archived rushing-yard forecast coverage and losses without tuning on holdout."""
import json
from collections import Counter
from pathlib import Path
from scripts.bridge_nfl_existing_prop_feeds import bridge

def diagnose(forecasts,outcomes):
    report=bridge(forecasts,outcomes)
    if report["status"]=="BLOCKED":return {"status":"BLOCKED","reason":report.get("reason")}
    lookup={r["snapshot_id"]:r for r in report["results"]}
    rows=[]
    for f in forecasts["forecasts"]:
        if f.get("market")!="player_rush_yds":continue
        scored=lookup.get(f["forecast_id"]+":over")
        if scored:
            rows.append({"forecast_id":f["forecast_id"],"game_id":f["event_id"],"player":f["player"],
                         "line":f["line"],"probability_over":f["model_probability"],
                         "bookmaker":f["bookmaker"],"outcome":scored["outcome"],
                         "brier":scored["brier"],"quoted_at":f["quoted_at"]})
    independent={(x["game_id"],x["player"]) for x in rows}
    return {"status":"RESEARCH_ONLY","bet_eligibility":"BLOCKED",
            "rush_over_graded":len(rows),
            "unique_player_game_outcomes":len(independent),
            "unique_games":len({x["game_id"] for x in rows}),
            "duplicate_bookmaker_exposure":len(rows)-len(independent),
            "rush_over_losses":sum(x["outcome"]=="loss" for x in rows),
            "by_player":dict(Counter(x["player"] for x in rows)),
            "by_bookmaker":dict(Counter(x["bookmaker"] for x in rows)),
            "cases":rows,
            "warning":"Descriptive diagnostics only; repeated players and bookmakers are correlated. Do not tune thresholds on this tiny observed subset."}
if __name__=="__main__":
    root=Path(__file__).resolve().parent.parent
    print(json.dumps(diagnose(json.loads((root/"feed/nfl_prop_forecast_ledger.json").read_text()),
                               json.loads((root/"feed/nfl_prop_verified_outcomes.json").read_text())),indent=2))
