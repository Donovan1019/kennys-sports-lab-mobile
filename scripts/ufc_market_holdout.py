#!/usr/bin/env python3
"""Evaluate point-in-time UFC moneyline odds against chronological Elo holdout.

Requires a separately curated archive of fight-level odds with verified provenance.
Never trusts caller-supplied aggregate model/market scores.
"""
import argparse
import json
import math
from pathlib import Path

def american_probability(odds):
    if type(odds) not in (int,float) or not math.isfinite(odds) or -100 < odds < 100:
        raise ValueError("Invalid American odds")
    return 100/(odds+100) if odds>0 else -odds/(-odds+100)

def score(predictions, odds_rows):
    # Historical baseline's forecasts contain only actual winners. To avoid
    # outcome leakage, compare all probabilities in the realized-winner direction.
    holdout=predictions[int(len(predictions)*0.8):]
    archive={}
    for row in odds_rows:
        if row.get("source_verified") is not True or row.get("pre_fight_verified") is not True:
            continue
        key=(row.get("event_id"),row.get("fight_id"))
        if key in archive:
            archive[key]=None  # duplicates invalidate this fight
        else:
            archive[key]=row
    matches=[]
    for prediction in holdout:
        row=archive.get((prediction["event_id"],prediction["fight_id"]))
        if not row or row.get("winner")!=prediction["winner"] or row.get("loser")!=prediction["loser"]:
            continue
        try:
            win=american_probability(row["winner_american_odds"])
            lose=american_probability(row["loser_american_odds"])
            p=prediction["winner_probability"]
            if not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<p<1:
                continue
            if win+lose<=0:
                continue
            market=win/(win+lose)
        except (KeyError,TypeError,ValueError,ZeroDivisionError):
            continue
        matches.append((p,market))
    def brier(index):
        return sum((1-x[index])**2 for x in matches)/len(matches) if matches else None
    def logloss(index):
        return sum(-math.log(max(1e-12,x[index])) for x in matches)/len(matches) if matches else None
    return {"independently_verified":False,
            "verification_status":"REQUIRES_EXTERNAL_SOURCE_AND_TIMESTAMP_AUDIT",
            "holdout_matched_fights":len(matches),
            "model_brier_on_matched":brier(0),"market_brier":brier(1),
            "model_log_loss_on_matched":logloss(0),"market_log_loss":logloss(1),
            "limitations":["Match-level source_verified flags are untrusted until independently audited",
                           "No betting certification without authenticated point-in-time odds provenance"]}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--elo-report",required=True)
    parser.add_argument("--archived-odds",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    report=json.loads(Path(args.elo_report).read_text())
    odds=json.loads(Path(args.archived_odds).read_text())
    if not isinstance(odds,dict) or not isinstance(odds.get("odds"),list):
        parser.error("Archived odds must contain an odds list")
    result=score(report["forecasts"],odds["odds"])
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
if __name__=="__main__":
    main()
