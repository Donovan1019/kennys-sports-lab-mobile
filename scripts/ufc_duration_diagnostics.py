#!/usr/bin/env python3
"""Historical UFC bout duration diagnostics with chronological holdout.

Observing a bout end does not reveal whether it ended by finish or decision.
This audit therefore DOES NOT estimate a finish hazard.
"""
import argparse,json,math
from collections import defaultdict
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join
from scripts.ufc_joined_chronological_rows import convert

def evaluate(rows,train_fraction=.8):
    if not 0<train_fraction<1:raise ValueError("invalid split")
    fights={}
    for row in rows:
        fid=str(row["fight_id"]);duration=float(row["active_seconds"])
        if not 0<duration<=1500 or not math.isfinite(duration):raise ValueError("invalid duration")
        if fid in fights:
            if fights[fid][0]!=row["fight_time"] or fights[fid][1]!=duration:
                raise ValueError("conflicting same-fight duration")
        else:fights[fid]=(row["fight_time"],duration)
    ordered=sorted(((date,fid,duration) for fid,(date,duration) in fights.items()))
    if len(ordered)<10:raise ValueError("insufficient fights")
    split=max(1,int(len(ordered)*train_fraction))
    cutoff=ordered[split][0]
    train=[x for x in ordered if x[0]<cutoff]
    test=[x for x in ordered if x[0]>=cutoff]
    if not train or not test:raise ValueError("empty chronological split")
    baseline=sum(x[2] for x in train)/len(train)
    def summary(data):
        ordered_d=sorted(x[2] for x in data)
        return {"n":len(data),"mean_seconds":sum(ordered_d)/len(ordered_d),
          "median_seconds":ordered_d[len(ordered_d)//2],
          "p10_seconds":ordered_d[int(.1*(len(ordered_d)-1))],
          "p90_seconds":ordered_d[int(.9*(len(ordered_d)-1))],
          "at_or_under_300s_fraction":sum(x<=300 for x in ordered_d)/len(ordered_d),
          "at_or_under_600s_fraction":sum(x<=600 for x in ordered_d)/len(ordered_d),
          "over_900s_fraction":sum(x>900 for x in ordered_d)/len(ordered_d)}
    return {"schema":1,"research_only":True,"bet_eligible":False,
       "finish_hazard_estimated":False,"scheduled_rounds_verified":False,
       "point_in_time_certified":False,"split_cutoff":cutoff,
       "train":summary(train),"test":summary(test),
       "train_mean_duration_baseline_seconds":baseline,
       "test_mean_absolute_error_seconds":sum(abs(x[2]-baseline) for x in test)/len(test),
       "test_mean_error_seconds":sum(baseline-x[2] for x in test)/len(test),
       "limitations":"Duration is observed retrospectively; no decision/finish labels or scheduled-round verification. Five-round and three-round fights are mixed. This is a distribution-shift diagnostic, not a trained finish hazard or valid pre-fight betting model."}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True);args=ap.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv");wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    joined=join(cross,wide)
    if joined["status"]!="JOINED":raise SystemExit("Fight ID join failed")
    converted=convert(joined["records"])
    report=evaluate(converted["rows"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"train":report["train"]["n"],"test":report["test"]["n"]}))
if __name__=="__main__":main()
