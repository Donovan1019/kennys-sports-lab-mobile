"""Audit whether fighter model-market disagreement predicts market forecast errors.

This is a retrospective, date-separated diagnostic, not a bet strategy.
"""
import math
from collections import defaultdict

def residual_audit(rows):
    days=sorted({r["date"] for r in rows})
    if len(days)<10:raise ValueError("insufficient independent dates")
    cutoff=days[int(.7*len(days))]
    train=[r for r in rows if r["date"]<cutoff]
    test=[r for r in rows if r["date"]>=cutoff]
    if len(train)<50 or len(test)<50:raise ValueError("insufficient paired fights")
    # Prespecified absolute model-market disagreement bins.
    edges=(0,.05,.10,.15,.20,1.01)
    def summary(batch):
        groups=defaultdict(list)
        for r in batch:
            m=r["market"];p=r["p"];y=r["y"]
            if not (0<m<1 and 0<p<1 and y in (0,1)):raise ValueError("invalid forecast")
            d=abs(p-m)
            idx=next(i for i in range(5) if edges[i]<=d<edges[i+1])
            groups[idx].append((m,p,y))
        output=[]
        for idx in range(5):
            group=groups[idx]
            if not group:
                output.append({"disagreement_range":[edges[idx],edges[idx+1]],"n":0})
                continue
            n=len(group)
            output.append({"disagreement_range":[edges[idx],edges[idx+1]],"n":n,
              "market_brier":sum((m-y)**2 for m,p,y in group)/n,
              "fighter_brier":sum((p-y)**2 for m,p,y in group)/n,
              "fighter_minus_market_brier":sum((p-y)**2-(m-y)**2 for m,p,y in group)/n,
              "fighter_signal_direction_accuracy":sum((p>m)==(y==1) for m,p,y in group)/n})
        return output
    return {"cutoff":cutoff,"selection_fights":len(train),"test_fights":len(test),
      "selection_bins":summary(train),"held_out_bins":summary(test),
      "bet_eligible":False,"provenance":"RETROSPECTIVE_CLOSING_MARKET_NOT_PIT_CERTIFIED",
      "interpretation":"Disagreement groups are diagnostic; no strategy thresholds fitted to held-out results."}
def main():
    import json
    from pathlib import Path
    from scripts.ufc_native_fight_join import BASE,fetch,join
    from scripts.ufc_joined_chronological_rows import convert
    from scripts.ufc_historical_prefix_features import build as prefix
    from scripts.ufc_opponent_walkforward import examples
    from scripts.ufc_defensive_features import enrich
    from scripts.ufc_defensive_ablation import predict
    cw,_=fetch(BASE+"id_crosswalk_all.csv")
    wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cw,wide)
    fighter=convert(linked["records"])
    base,_=examples(linked["records"],prefix(fighter["rows"]))
    defensive,_=enrich(base,linked["records"])
    report=residual_audit(list(predict(defensive,linked["records"]).values()))
    Path("ufc_market_residual_audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
