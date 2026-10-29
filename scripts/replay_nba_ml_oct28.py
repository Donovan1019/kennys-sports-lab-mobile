#!/usr/bin/env python3
"""Point-in-time October 28 NBA moneyline slip replay; research only."""
import json
import math
import pathlib

ARCHIVE = pathlib.Path("data/nba_ml_odds_archive/2026-10-28/20261028T220301Z.json")
PICKS = {
    "Atlanta Hawks": False,
    "Cleveland Cavaliers": True,
    "Minnesota Timberwolves": False,
    "Oklahoma City Thunder": False,
    "Orlando Magic": False,
}

def replay(archive):
    rows = archive.get("rows", [])
    stamp = archive.get("captured_at", "")
    if archive.get("status") != "ok" or not stamp:
        raise ValueError("Unverified pregame archive")
    output = []
    for team, won in PICKS.items():
        candidates = [r for r in rows if r.get("selection") == team and
                      r.get("bookmaker") == "fanduel"]
        if len(candidates) != 1:
            raise ValueError("Missing or duplicate pregame reference quote: " + team)
        r = candidates[0]
        if r.get("quote_updated_at", "") > r.get("commence_time", "") or stamp >= r.get("commence_time", ""):
            raise ValueError("Post-tipoff data rejected: " + team)
        p = r.get("model_probability")
        if not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 < p < 1:
            raise ValueError("Invalid archived model probability: " + team)
        price = r["price"]
        dec = 1 + (100 / -price if price < 0 else price / 100)
        output.append({"team": team, "won": won, "model_probability": p,
                       "reference_book": "fanduel", "reference_price": price,
                       "single_leg_reference_ev": round(p * dec - 1, 5),
                       "brier": round((p - int(won)) ** 2, 6),
                       "event_id": r["event_id"]})
    return {"status": "research_only", "date_et": "2026-10-28",
            "archive_captured_at": stamp, "source": str(ARCHIVE),
            "slip_source": "user-reported Onyx five-leg +1264, $5, 1/5 winners",
            "warning": "FanDuel prices are reference quotes, not executable Onyx prices; archived probabilities are not independently verified as the exact on-screen selection-time probabilities. Do not treat as a validated backtest or use to approve betting readiness.",
            "wins": sum(p["won"] for p in output), "legs": len(output),
            "mean_brier": round(sum(p["brier"] for p in output) / len(output), 6),
            "picks": output}

def main():
    result = replay(json.loads(ARCHIVE.read_text()))
    path = pathlib.Path("backtests/results/2026-10-28/nba_ml_slip_replay.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print("NBA ML replay:", result["wins"], "/", result["legs"], "mean Brier", result["mean_brier"])

if __name__ == "__main__":
    main()
