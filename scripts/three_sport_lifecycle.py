"""Three-sport forecast lifecycle readiness audit; no paid API access."""
import json
from pathlib import Path
from scripts.three_sport_champion import SPORTS

def inspect(sport, feeds):
    ledger=feeds.get("forecast_ledger",{})
    outcomes=feeds.get("forecast_outcomes",{})
    baseline=feeds.get("market_baseline_ledger",{})
    consensus=feeds.get("market_consensus",{})
    champion=feeds.get("champion_challenger",{})
    forecasts=ledger.get("forecasts",[])
    scored=outcomes.get("scored",[])
    baselines=baseline.get("baselines",[])
    verified=[r for r in baselines if r.get("status")=="verified_pregame_quote"]
    paired=champion.get("verified_paired_games",0)
    blockers=[]
    if not forecasts: blockers.append("no_immutable_pregame_forecasts")
    if not consensus.get("events"): blockers.append("no_eligible_multi_book_consensus")
    if forecasts and not verified: blockers.append("no_verified_quote_time_matched_baselines")
    if forecasts and not scored: blockers.append("no_verified_completed_forecast_matches")
    if scored and not paired: blockers.append("no_scored_forecast_market_pairs")
    return {"sport":sport,"status":"paired_evaluation_available" if paired else "awaiting_verified_pairs",
            "immutable_forecasts":len(forecasts),"scored_forecasts":len(scored),
            "consensus_events":len(consensus.get("events",[])),
            "verified_market_baselines":len(verified),"verified_paired_games":paired,
            "blockers":blockers,
            "note":"A successful workflow is not evidence of predictive advantage."}

def main():
    reports=[]
    for sport in SPORTS:
        feeds={}
        for suffix in ("forecast_ledger","forecast_outcomes","market_baseline_ledger",
                       "market_consensus","champion_challenger"):
            path=Path(f"feed/{sport}_{suffix}.json")
            if path.exists():
                feeds[suffix]=json.loads(path.read_text())
        report=inspect(sport,feeds)
        reports.append(report)
        print(f"{sport}: {report['status']} forecasts={report['immutable_forecasts']} scored={report['scored_forecasts']} paired={report['verified_paired_games']} blockers={','.join(report['blockers']) or 'none'}")
    Path("feed/three_sport_lifecycle_readiness.json").write_text(
        json.dumps({"status":"research_only","sports":reports},indent=2)+"\n")
if __name__=="__main__":
    main()
