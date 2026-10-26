#!/usr/bin/env python3
"""Research-only, forward snapshot performance dashboard. No betting recommendations."""
import json,sys
from pathlib import Path
from collections import defaultdict
from scripts.bridge_nfl_existing_prop_feeds import bridge,MARKETS

def dashboard(forecasts,outcomes):
    report=bridge(forecasts,outcomes)
    if report["status"]=="BLOCKED":return {"status":"BLOCKED","bridge_report":report,"bet_eligibility":"BLOCKED"}
    indexed={r["snapshot_id"]:r for r in report["results"]}
    grouped=defaultdict(list)
    for f in forecasts["forecasts"]:
        if f.get("market") not in MARKETS:continue
        key=f["forecast_id"]+":over"
        if key in indexed:grouped[f["market"]].append(indexed[key])
    markets={}
    unique_outcomes={(f["event_id"],f["player"],f["market"]) for f in forecasts["forecasts"] if f.get("market") in MARKETS and f["forecast_id"]+":over" in indexed}
    for market,rows in sorted(grouped.items()):
        scored=[r for r in rows if r["brier"] is not None]
        distinct={(f["event_id"],f["player"]) for f in forecasts["forecasts"] if f.get("market")==market and f["forecast_id"]+":over" in indexed}
        markets[market]={"graded_over_forecasts":len(rows),
            "unique_player_game_outcomes":len(distinct),
            "wins":sum(r["outcome"]=="win" for r in rows),
            "losses":sum(r["outcome"]=="loss" for r in rows),
            "pushes":sum(r["outcome"]=="push" for r in rows),
            "brier":round(sum(r["brier"] for r in scored)/len(scored),6) if scored else None,
            "hypothetical_units":round(sum(r["units"] for r in rows),6),
            "eligibility":"BLOCKED"}
    return {"status":"RESEARCH_ONLY","bet_eligibility":"BLOCKED",
        "coverage":report["bridge"],"total_graded_sides":report["graded"],
        "total_pending_sides":report["pending"],
        "unique_player_game_market_outcomes":len(unique_outcomes),
        "unique_games_with_results":len({g for g,_,_ in unique_outcomes}),"markets":markets,
        "warning":"Over-only descriptive scoring avoids treating opposing sides of one forecast as independent bets. Archived forecasts are not documented actual wagers; ROI and profitability cannot be inferred. Small matched sample and missing outcomes prevent readiness."}

if __name__=="__main__":
    root=Path(__file__).resolve().parent.parent
    data=dashboard(json.loads((root/"feed/nfl_prop_forecast_ledger.json").read_text()),
                   json.loads((root/"feed/nfl_prop_verified_outcomes.json").read_text()))
    print(json.dumps(data,indent=2))
    if data["status"]=="BLOCKED":sys.exit(1)
