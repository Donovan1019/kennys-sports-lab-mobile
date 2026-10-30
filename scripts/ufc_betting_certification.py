#!/usr/bin/env python3
"""Fail-closed UFC betting certification gate, separate from Elo research evaluation."""
import argparse
import json
import math
from pathlib import Path

def certify(report, market=None, min_holdout=200):
    failures=[]
    n=report.get("holdout_evaluated_fights",0)
    brier=report.get("holdout_brier")
    loss=report.get("holdout_log_loss")
    if not isinstance(n,int) or n<min_holdout:
        failures.append("insufficient chronological holdout")
    if not isinstance(brier,(int,float)) or not math.isfinite(brier) or brier>=0.25:
        failures.append("holdout Brier does not beat 50% reference")
    if not isinstance(loss,(int,float)) or not math.isfinite(loss) or loss>=math.log(2):
        failures.append("holdout log loss does not beat 50% reference")
    if report.get("holdout_status")!="CHRONOLOGICAL_EVALUATION_ONLY":
        failures.append("chronological holdout unavailable")
    # The 50% reference is not the sportsbook baseline: certification
    # additionally requires point-in-time, independently sourced odds.
    if not isinstance(market,dict) or market.get("independently_verified") is not True:
        failures.append("independently verified archived sportsbook odds missing")
    else:
        for key in ("holdout_matched_fights","market_brier","market_log_loss","model_brier_on_matched","model_log_loss_on_matched"):
            value=market.get(key)
            if not isinstance(value,(int,float)) or not math.isfinite(value):
                failures.append("missing market comparison: "+key)
        if not failures:
            if market["holdout_matched_fights"]<min_holdout:
                failures.append("insufficient point-in-time odds matched holdout")
            if market["model_brier_on_matched"]>=market["market_brier"]:
                failures.append("model does not beat market Brier")
            if market["model_log_loss_on_matched"]>=market["market_log_loss"]:
                failures.append("model does not beat market log loss")
    return {"certified":not failures,"bet_eligible":not failures,
            "status":"CERTIFIED" if not failures else "NOT_CERTIFIED",
            "failures":failures,"holdout_evaluated_fights":n,
            "holdout_brier":brier,"holdout_log_loss":loss,
            "scope":"UFC Elo moneyline only; not individual picks or other markets"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",required=True)
    p.add_argument("--market-comparison")
    p.add_argument("--output",required=True)
    p.add_argument("--minimum-holdout",type=int,default=200)
    args=p.parse_args()
    if args.minimum_holdout<1:
        p.error("minimum holdout must be positive")
    report=json.loads(Path(args.report).read_text())
    market=json.loads(Path(args.market_comparison).read_text()) if args.market_comparison else None
    verdict=certify(report,market,args.minimum_holdout)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(verdict,indent=2)+"\n")
    print(json.dumps(verdict))
    if not verdict["certified"]:
        raise SystemExit(1)
if __name__=="__main__":
    main()
