"""Nested chronological validation of market+fighter UFC probability blending.

Blend weight is selected on earlier event dates only; evaluation is strictly
later dates. Closing market is not an executable pre-fight price.
"""
import hashlib,math
from collections import defaultdict
from scripts.ufc_market_benchmark import market_probability
from scripts.ufc_opponent_walkforward import sigmoid

def collect(rows,records,lr=.04,reg=.0005):
    lookup={r["ufcstats_fight_id"]:r for r in records}
    groups=defaultdict(list)
    for row in rows:groups[row["date"]].append(row)
    weights=[0.0]*4;paired=[]
    for day in sorted(groups):
        batch=groups[day]
        for row in batch:
            record=lookup.get(row["fight_id"])
            if not record:continue
            market=market_probability(record)
            if market is None:continue
            model=sigmoid(weights[0]+sum(w*x for w,x in zip(weights[1:],row["x"])))
            if int(hashlib.sha256(row["fight_id"].encode()).hexdigest(),16)%2:market=1-market
            paired.append({"date":day,"model":model,"market":market,"y":row["y"]})
        # Update only after same-day predictions have been generated.
        for row in batch:
            x=[1.0]+row["x"]
            p=sigmoid(sum(w*v for w,v in zip(weights,x)))
            for i in range(4):
                weights[i]-=lr*((p-row["y"])*x[i]+(reg*weights[i] if i else 0))
    return paired
def blend_score(paired):
    days=sorted({x["date"] for x in paired})
    if len(days)<10:raise ValueError("insufficient event dates")
    cutoff=days[int(len(days)*.7)]
    train=[r for r in paired if r["date"]<cutoff]
    test=[r for r in paired if r["date"]>=cutoff]
    if len(train)<50 or len(test)<20:raise ValueError("insufficient paired fights")
    def prob(r,w):return w*r["model"]+(1-w)*r["market"]
    def brier(batch,w):return sum((prob(r,w)-r["y"])**2 for r in batch)/len(batch)
    candidates=[i/20 for i in range(21)]
    selected=min(candidates,key=lambda w:(brier(train,w),w))
    market=brier(test,0)
    blend=brier(test,selected)
    return {"selection_cutoff":cutoff,"weight_selected_from_prior_dates":selected,
        "selection_fights":len(train),"held_out_fights":len(test),
        "held_out_market_brier":market,"held_out_blend_brier":blend,
        "held_out_blend_minus_market":blend-market,
        "beats_market_held_out":blend<market,
        "provenance":"RETROSPECTIVE_CLOSING_MARKET_NOT_PIT_CERTIFIED",
        "bet_eligible":False,
        "warning":"Blend weight tuned only on earlier dates; closing odds are not actionable pre-fight quotes."}
