"""Immutable pregame market baseline capture and three-sport champion evaluation.

No historical market quotes are reconstructed after kickoff. Challenger status
is research-only and requires paired, verified outcomes before comparison.
"""
import json
import math
from pathlib import Path
from scripts.forecast_ledger import timestamp

SPORTS=("basketball_nba","icehockey_nhl","americanfootball_nfl")

def capture(existing,ledger,consensus):
    entries={r["forecast_id"]:r for r in existing.get("baselines",[]) if r.get("forecast_id")}
    quotes={r.get("event_id"):r for r in consensus.get("events",[]) if r.get("event_id")}
    added=0
    for f in ledger.get("forecasts",[]):
        fid=f.get("forecast_id")
        if not fid or fid in entries:
            continue
        q=quotes.get(f.get("event_id"))
        if not q or type(q.get("bookmaker_count")) is not int or q["bookmaker_count"]<2:
            continue
        p=q.get("home_consensus_no_vig")
        start=timestamp(f.get("event_start"))
        captured=timestamp(f.get("forecast_at"))
        if type(p) not in (int,float) or not math.isfinite(p) or not 0<p<1 or not start or not captured or captured>=start:
            continue
        # Consensus summaries lack per-quote timestamp; never infer that an
        # old summary was available at the historical forecast timestamp.
        # Only attach to forecasts captured in this same collection cycle.
        entries[fid]={"forecast_id":fid,"event_id":f["event_id"],
                      "home_probability":p,"source":"multi_book_no_vig_consensus",
                      "forecast_at":f["forecast_at"],"event_start":f["event_start"],
                      "status":"unverified_quote_time_research_only"}
        added+=1
    return {"status":"research_only_unverified_quote_timing","baselines":list(entries.values()),"added":added}

def evaluate(outcomes,baselines,*,minimum=100):
    lookup={r.get("forecast_id"):r for r in baselines.get("baselines",[])}
    paired=[]
    for r in outcomes.get("scored",[]):
        b=lookup.get(r.get("forecast_id"))
        if not b or b.get("status")!="verified_pregame_quote":
            continue
        p=r.get("home_probability")
        q=b.get("home_probability")
        y=r.get("home_won")
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in (p,q)) or not 0<p<1 or not 0<q<1 or type(y) is not int or y not in (0,1):
            continue
        paired.append(((p-y)**2,(q-y)**2))
    n=len(paired)
    model=sum(x for x,_ in paired)/n if n else None
    market=sum(y for _,y in paired)/n if n else None
    return {"status":"research_only","verified_paired_games":n,
            "model_brier":round(model,6) if n else None,
            "market_brier":round(market,6) if n else None,
            "model_minus_market_brier":round(model-market,6) if n else None,
            "minimum_games_for_review":minimum,
            "promotion_approved":False,
            "reason":"Insufficient verified paired pregame quotes" if n<minimum else "Independent holdout and statistical review required",
            "warning":"Consensus snapshot timestamps are not presently persisted; do not treat them as verified contemporaneous market baselines."}

def main():
    for sport in SPORTS:
        ledger_path=Path(f"feed/{sport}_forecast_ledger.json")
        consensus_path=Path(f"feed/{sport}_market_consensus.json")
        outcome_path=Path(f"feed/{sport}_forecast_outcomes.json")
        if not ledger_path.exists() or not consensus_path.exists():
            print(f"{sport}: benchmark inputs unavailable")
            continue
        baseline_path=Path(f"feed/{sport}_market_baseline_ledger.json")
        old=json.loads(baseline_path.read_text()) if baseline_path.exists() else {}
        ledger=json.loads(ledger_path.read_text())
        consensus=json.loads(consensus_path.read_text())
        baselines=capture(old,ledger,consensus)
        added=baselines.pop("added")
        if added:
            baseline_path.write_text(json.dumps(baselines,indent=2)+"\n")
        outcomes=json.loads(outcome_path.read_text()) if outcome_path.exists() else {}
        report=evaluate(outcomes,baselines)
        Path(f"feed/{sport}_champion_challenger.json").write_text(json.dumps(report,indent=2)+"\n")
        print(f"{sport}: market benchmark candidate snapshots={added}, verified paired={report['verified_paired_games']}")
if __name__=="__main__":
    main()
