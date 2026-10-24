"""Ablation test: whether historical defensive UFC features improve market-relative scores."""
import hashlib,json,math
from collections import defaultdict
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join
from scripts.ufc_joined_chronological_rows import convert
from scripts.ufc_historical_prefix_features import build as prefix
from scripts.ufc_opponent_walkforward import examples,sigmoid
from scripts.ufc_defensive_features import enrich
from scripts.ufc_market_benchmark import market_probability

def predict(rows,records,lr=.04,reg=.0005):
    lookup={r["ufcstats_fight_id"]:r for r in records}
    groups=defaultdict(list)
    for row in rows:groups[row["date"]].append(row)
    weights=[0.]*(len(rows[0]["x"])+1)
    paired=[]
    for day in sorted(groups):
        batch=groups[day]
        for row in batch:
            rec=lookup.get(row["fight_id"])
            market=market_probability(rec) if rec else None
            if market is None:continue
            model=sigmoid(sum(w*v for w,v in zip(weights,[1]+row["x"])))
            if int(hashlib.sha256(row["fight_id"].encode()).hexdigest(),16)%2:market=1-market
            paired.append({"date":day,"fight_id":row["fight_id"],"p":model,"market":market,"y":row["y"]})
        for row in batch:
            x=[1]+row["x"]
            p=sigmoid(sum(w*v for w,v in zip(weights,x)))
            for i in range(len(weights)):
                weights[i]-=lr*((p-row["y"])*x[i]+(reg*weights[i] if i else 0))
    return {r["fight_id"]:r for r in paired}
def ablation(base,extended,records):
    base_preds=predict(base,records)
    ext_preds=predict(extended,records)
    common=sorted(set(base_preds)&set(ext_preds))
    days=sorted({base_preds[fid]["date"] for fid in common})
    if len(days)<10:raise ValueError("insufficient matched event dates")
    cutoff=days[int(.7*len(days))]
    test=[fid for fid in common if base_preds[fid]["date"]>=cutoff]
    if len(test)<100:raise ValueError("insufficient held-out fights")
    def brier(pred,key):return sum((pred[fid][key]-pred[fid]["y"])**2 for fid in test)/len(test)
    return {"cutoff":cutoff,"matched_test_fights":len(test),
      "market_brier":brier(base_preds,"market"),
      "original_model_brier":brier(base_preds,"p"),
      "defensive_model_brier":brier(ext_preds,"p"),
      "incremental_brier_change":brier(ext_preds,"p")-brier(base_preds,"p"),
      "defensive_beats_market":brier(ext_preds,"p")<brier(base_preds,"market"),
      "bet_eligible":False,"provenance":"RETROSPECTIVE_NOT_PIT_CERTIFIED"}
def main():
    cross,_=fetch(BASE+"id_crosswalk_all.csv")
    wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    fighter=convert(linked["records"])
    base,_=examples(linked["records"],prefix(fighter["rows"]))
    extended,missing=enrich(base,linked["records"])
    result=ablation(base,extended,linked["records"])
    result["excluded_defensive_features"]=missing
    Path("ufc_defensive_ablation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
