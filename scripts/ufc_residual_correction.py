"""Train-only residual correction to historical UFC closing-market probabilities.

No closing-odds result is used for model training on its own event date.
Correction strength is selected on chronological validation dates; an untouched
later test window evaluates against market-only. Retrospective research only.
"""
import json,math
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join
from scripts.ufc_joined_chronological_rows import convert
from scripts.ufc_historical_prefix_features import build as prefix
from scripts.ufc_opponent_walkforward import examples
from scripts.ufc_defensive_features import enrich
from scripts.ufc_defensive_ablation import predict

def assess(rows):
    days=sorted({r["date"] for r in rows})
    if len(days)<20:raise ValueError("insufficient independent dates")
    cut1=days[int(.5*len(days))]
    cut2=days[int(.7*len(days))]
    train=[r for r in rows if r["date"]<cut1]
    validation=[r for r in rows if cut1<=r["date"]<cut2]
    test=[r for r in rows if r["date"]>=cut2]
    if min(len(train),len(validation),len(test))<50:raise ValueError("insufficient split size")
    def correction(r,w):
        # Shrink model-market residual, preserving the closing market as baseline.
        return min(.999999,max(.000001,r["market"]+w*(r["p"]-r["market"])))
    def brier(batch,w):
        return sum((correction(r,w)-r["y"])**2 for r in batch)/len(batch)
    # Fixed, nonnegative correction weights. Zero means market-only.
    choices=[i/100 for i in range(0,51,5)]
    # Validation selects a single weight; no test outcome affects selection.
    selected=min(choices,key=lambda w:(brier(validation,w),w))
    return {"training_window_fights":len(train),
       "validation_window_fights":len(validation),
       "untouched_test_fights":len(test),
       "validation_start":cut1,"test_start":cut2,
       "selected_residual_weight":selected,
       "validation_market_brier":brier(validation,0),
       "validation_corrected_brier":brier(validation,selected),
       "test_market_brier":brier(test,0),
       "test_corrected_brier":brier(test,selected),
       "test_delta_brier":brier(test,selected)-brier(test,0),
       "improves_held_out_market":brier(test,selected)<brier(test,0),
       "bet_eligible":False,
       "provenance":"RETROSPECTIVE_CLOSING_MARKET_NOT_PIT_CERTIFIED",
       "limitations":"Closing market is unavailable as a historical executable pre-fight price; no ROI or causal edge inference."}
def main():
    cw,_=fetch(BASE+"id_crosswalk_all.csv")
    wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cw,wide)
    fighter=convert(linked["records"])
    base,_=examples(linked["records"],prefix(fighter["rows"]))
    defensive,_=enrich(base,linked["records"])
    rows=list(predict(defensive,linked["records"]).values())
    result=assess(rows)
    Path("ufc_residual_correction.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
