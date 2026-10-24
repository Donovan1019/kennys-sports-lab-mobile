"""Compare out-of-sample UFC win predictions to historical no-vig market probabilities.

Market data is retrospective and closing odds are a benchmark, NOT an
executable pre-fight bet price or evidence of profitability.
"""
import math
from collections import defaultdict
from scripts.ufc_opponent_walkforward import sigmoid

def market_probability(row):
    f=row["wide_record"]
    try:
        p=float(f["f1_close_prob_novig"])
        q=float(f["f2_close_prob_novig"])
    except (ValueError,TypeError,KeyError):
        return None
    if not all(math.isfinite(v) and 0<v<1 for v in (p,q)):
        return None
    if abs(p+q-1)>.025:
        return None
    return p/(p+q)

def benchmark(rows,records,train_fraction=.7,lr=.04,reg=.0005):
    lookup={r["ufcstats_fight_id"]:r for r in records}
    days=sorted({r["date"] for r in rows})
    if len(days)<4:raise ValueError("insufficient event dates")
    cutoff=days[max(1,min(len(days)-1,int(len(days)*train_fraction)))]
    groups=defaultdict(list)
    for row in rows:groups[row["date"]].append(row)
    weights=[0.0]*4
    paired=[];unpaired=0
    for day in days:
        batch=groups[day]
        if day>=cutoff:
            for row in batch:
                record=lookup.get(row["fight_id"])
                if not record:unpaired+=1;continue
                market=market_probability(record)
                if market is None:unpaired+=1;continue
                model=sigmoid(weights[0]+sum(w*x for w,x in zip(weights[1:],row["x"])))
                # Walkforward examples randomly swap fighter orientation by fight ID.
                # The market always refers to source-native f1; reverse consistently.
                import hashlib
                if int(hashlib.sha256(row["fight_id"].encode()).hexdigest(),16)%2:
                    market=1-market
                paired.append((model,market,row["y"],day))
        else:
            for row in batch:
                x=[1.0]+row["x"]
                p=sigmoid(sum(w*v for w,v in zip(weights,x)))
                for i in range(4):
                    weights[i]-=lr*((p-row["y"])*x[i]+(reg*weights[i] if i else 0))
    if not paired:raise ValueError("no market-linked test predictions")
    def brier(k):return sum((t[k]-t[2])**2 for t in paired)/len(paired)
    def logloss(k):
        return -sum(y*math.log(max(1e-12,t[k]))+(1-y)*math.log(max(1e-12,1-t[k]))
                    for t in paired for y in [t[2]])/len(paired)
    from scripts.ufc_market_gap_uncertainty import cluster_bootstrap
    uncertainty=cluster_bootstrap(paired)
    return {"paired_market_uncertainty":uncertainty,"test_cutoff":cutoff,"paired_test_fights":len(paired),"unpaired_test_fights":unpaired,
       "model_brier":brier(0),"market_brier":brier(1),
       "model_log_loss":logloss(0),"market_log_loss":logloss(1),
       "model_brier_minus_market":brier(0)-brier(1),
       "market_type":"RETROSPECTIVE_CLOSING_NO_VIG",
       "profitability_tested":False,"bet_eligible":False,
       "caveat":"Closing market is a predictive benchmark only; no executable historical bet quotes, CLV, or verified point-in-time snapshot."}
