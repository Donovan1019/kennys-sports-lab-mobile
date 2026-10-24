"""Chronological market+defensive-model blend, with strictly later holdout.

Defensive fighter model is trained online, predicting each card before updates.
The blend weight is selected using earlier event dates, never test outcomes.
Closing market is research-only and not an executable pre-fight quote.
"""
import json
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join
from scripts.ufc_joined_chronological_rows import convert
from scripts.ufc_historical_prefix_features import build as prefix
from scripts.ufc_opponent_walkforward import examples
from scripts.ufc_defensive_features import enrich
from scripts.ufc_defensive_ablation import predict

def score(rows):
    days=sorted({r["date"] for r in rows})
    if len(days)<10:raise ValueError("insufficient event dates")
    cutoff=days[int(.7*len(days))]
    train=[r for r in rows if r["date"]<cutoff]
    test=[r for r in rows if r["date"]>=cutoff]
    if len(train)<50 or len(test)<20:raise ValueError("insufficient fights")
    def brier(batch,weight):
        return sum((weight*r["p"]+(1-weight)*r["market"]-r["y"])**2 for r in batch)/len(batch)
    choices=[i/20 for i in range(21)]
    weight=min(choices,key=lambda w:(brier(train,w),w))
    return {"cutoff":cutoff,"selection_fights":len(train),"test_fights":len(test),
      "selected_defensive_model_weight":weight,"selected_market_weight":1-weight,
      "test_market_brier":brier(test,0),
      "test_blend_brier":brier(test,weight),
      "test_blend_minus_market":brier(test,weight)-brier(test,0),
      "beats_market_held_out":brier(test,weight)<brier(test,0),
      "bet_eligible":False,"provenance":"RETROSPECTIVE_CLOSING_MARKET_NOT_PIT_CERTIFIED"}
def main():
    cw,_=fetch(BASE+"id_crosswalk_all.csv")
    wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cw,wide)
    fighter=convert(linked["records"])
    base,_=examples(linked["records"],prefix(fighter["rows"]))
    defensive,excluded=enrich(base,linked["records"])
    result=score(list(predict(defensive,linked["records"]).values()))
    result["excluded_fights"]=excluded
    Path("ufc_defensive_market_blend.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
