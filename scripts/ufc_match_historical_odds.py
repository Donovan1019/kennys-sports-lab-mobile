#!/usr/bin/env python3
"""Cross-source historical UFC bout-to-odds matching; retrospective, NOT betting certified."""
import argparse
import json
import math
from collections import Counter
from pathlib import Path

def match(bouts, candidates, forecasts):
    # Exact normalized event date, event name and unordered fighter pair.
    # No fuzzy matching or winner-dependent selection.
    def norm(s):
        return " ".join(str(s).casefold().strip().split())
    index={}
    for c in candidates:
        key=(norm(c["event_date"][:10]),norm(c["event_name"]),tuple(sorted((norm(c["winner"]),norm(c["loser"])))))
        index.setdefault(key,[]).append(c)
    matched={}
    rejected=Counter()
    for b in bouts:
        key=(norm(b["event_date"][:10]),norm(b["event_id"]),tuple(sorted((norm(b["winner"]),norm(b["loser"])))))
        options=index.get(key,[])
        if len(options)!=1:
            rejected["missing_or_ambiguous_match"]+=1
            continue
        c=options[0]
        if norm(b["winner"])!=norm(c["winner"]) or norm(b["loser"])!=norm(c["loser"]):
            rejected["winner_disagreement"]+=1
            continue
        matched[(b["event_id"],b["fight_id"])]=c
    cutoff=int(len(forecasts)*0.8)
    holdout=forecasts[cutoff:]
    pairs=[]
    retrospective_pairs=[]
    for f in forecasts:
        c=matched.get((f["event_id"],f["fight_id"]))
        if c is None:
            continue
        p=f["winner_probability"]
        try:
            q1=1/float(c["winner_decimal_odds"])
            q2=1/float(c["loser_decimal_odds"])
            market=q1/(q1+q2)
            if not (0<p<1 and 0<market<1 and math.isfinite(p)):
                raise ValueError()
        except (ValueError,TypeError,ZeroDivisionError,KeyError):
            rejected["invalid_probabilities"]+=1
            continue
        retrospective_pairs.append((p,market))
        if f in holdout:
            pairs.append((p,market))
    matched_dates=sorted(b["event_date"][:10] for b in bouts if (b["event_id"],b["fight_id"]) in matched)
    odds_dates=sorted(c["event_date"][:10] for c in candidates)
    holdout_dates=sorted(f["start_time"][:10] for f in holdout)
    def bounds(xs):
        return [xs[0],xs[-1]] if xs else [None,None]
    def metrics(rows,i):
        return {"brier":sum((1-x[i])**2 for x in rows)/len(rows) if rows else None,
                "log_loss":sum(-math.log(x[i]) for x in rows)/len(rows) if rows else None}
    return {"status":"RETROSPECTIVE_ONLY_NOT_CERTIFIED","bet_eligible":False,
            "source_odds_pre_fight_verified":False,
            "historical_bouts":len(bouts),"odds_candidates":len(candidates),
            "exact_matched_bouts":len(matched),"strict_cohort_holdout":len(holdout),
            "matched_holdout":len(pairs),"excluded":dict(rejected),
            "date_ranges":{"odds":bounds(odds_dates),"matched":bounds(matched_dates),"holdout":bounds(holdout_dates)},
            "matched_strict_cohort":sum((f["event_id"],f["fight_id"]) in matched for f in forecasts),
            "model":metrics(pairs,0),"market_no_vig":metrics(pairs,1),
            "retrospective_all_periods":{"status":"DESCRIPTIVE_IN_SAMPLE_ONLY",
                "matched_scored":len(retrospective_pairs),
                "model":metrics(retrospective_pairs,0),
                "market_no_vig":metrics(retrospective_pairs,1)},
            "limitations":["Retrospective scrape timestamps are not independently verified pre-fight prices",
                           "Exact-match coverage is not betting certification",
                           "All-period matched comparisons are NOT a held-out market validation",
                           "Scoring is descriptive and must not be used for live bet eligibility"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--bouts",required=True)
    p.add_argument("--odds",required=True)
    p.add_argument("--elo-report",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    bouts=json.loads(Path(a.bouts).read_text())["results"]
    odds=json.loads(Path(a.odds).read_text())["odds_candidates"]
    forecasts=json.loads(Path(a.elo_report).read_text())["forecasts"]
    report=match(bouts,odds,forecasts)
    Path(a.output).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
if __name__=="__main__":
    main()
