#!/usr/bin/env python3
"""Research-only chronological UFC duration uncertainty coverage audit.

Prequential intervals use only earlier-date observed baseline residuals.
No future or same-day holdout leakage. Coverage is descriptive, not calibrated.
"""
import argparse,json
from collections import defaultdict
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join

def quantile(values,p):
    if not values:raise ValueError("empty residual history")
    ordered=sorted(values)
    return ordered[min(len(ordered)-1,max(0,int((len(ordered)-1)*p+0.999999999)))]
def evaluate(records,train_fraction=.8,min_prior=3,min_residuals=30):
    if not 0<train_fraction<1 or min_prior<1 or min_residuals<1:raise ValueError("invalid parameters")
    fights=[]
    for record in records:
        f=record["wide_record"]
        try:
            day=str(f["event_date"])[:10];a=str(f["f1_id"]).strip().lower()
            b=str(f["f2_id"]).strip().lower();duration=float(f["fight_duration_sec"])
        except (ValueError,KeyError,TypeError):continue
        if not a or not b or a==b or not 0<duration<=1500 or len(day)!=10:continue
        fights.append((day,record["ufcstats_fight_id"],a,b,duration))
    fights.sort()
    if len(fights)<10:raise ValueError("insufficient fights")
    cutoff=fights[int(len(fights)*train_fraction)][0]
    if cutoff==fights[0][0]:raise ValueError("no prior training date")
    history=defaultdict(list);residuals=[];holdout=[];excluded=defaultdict(int)
    for day in sorted({v[0] for v in fights}):
        batch=[v for v in fights if v[0]==day]
        updates=[]
        for _,fid,a,b,actual in batch:
            x=history[a];y=history[b]
            if len(x)<min_prior or len(y)<min_prior:
                if day>=cutoff:excluded["insufficient_fighter_history"]+=1
                continue
            predicted=(sum(x)/len(x)+sum(y)/len(y))/2
            # Interval width is frozen before any fights from this day are settled.
            if day>=cutoff:
                if len(residuals)<min_residuals:
                    excluded["insufficient_prior_residuals"]+=1
                else:
                    width=quantile(residuals,.8)
                    holdout.append((fid,predicted,actual,width))
            updates.append(abs(predicted-actual))
        # Same-day fights do not contribute to any predictions on this date.
        residuals.extend(updates)
        for _,_,a,b,actual in batch:
            history[a].append(actual);history[b].append(actual)
    def summarize(items):
        count=len(items)
        if not count:return {"fights":0,"coverage":None,"mean_half_width_seconds":None,"mean_absolute_error_seconds":None}
        return {"fights":count,"coverage":sum(abs(p-y)<=w for _,p,y,w in items)/count,
          "mean_half_width_seconds":sum(w for _,p,y,w in items)/count,
          "mean_absolute_error_seconds":sum(abs(p-y) for _,p,y,w in items)/count}
    duration_bins={"under_5_minutes":[],"5_to_10_minutes":[],"10_to_15_minutes":[],"15_minutes_plus":[]}
    for item in holdout:
        forecast=item[1]
        label="under_5_minutes" if forecast<300 else "5_to_10_minutes" if forecast<600 else "10_to_15_minutes" if forecast<900 else "15_minutes_plus"
        duration_bins[label].append(item)
    n=len(holdout)
    covered=sum(abs(p-y)<=w for _,p,y,w in holdout)
    return {"schema":1,"holdout_start_date":cutoff,"evaluated_fights":n,
      "target_nominal_coverage":.8,
      "coverage_by_predicted_duration":{name:summarize(items) for name,items in duration_bins.items()},
      "coverage_by_predicted_duration_uses_only_forecast":True,
      "empirical_coverage":covered/n if n else None,
      "mean_half_width_seconds":sum(w for _,p,y,w in holdout)/n if n else None,
      "mean_absolute_error_seconds":sum(abs(p-y) for _,p,y,w in holdout)/n if n else None,
      "excluded":dict(excluded),"interval_method":"expanding earlier-date absolute-residual empirical 80th percentile",
      "point_in_time_certified":False,"calibrated":False,"bet_eligible":False,
      "production_promotion_allowed":False,
      "limitations":"Research diagnostic; retrospective capture, no PIT verification. Coverage bins use only predicted duration, not realized outcome; small bins can be unstable. Empirical coverage is not guaranteed calibration; no fight-format source semantics assumed."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv");wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    if linked["status"]!="JOINED":raise SystemExit("fight join failed")
    result=evaluate(linked["records"])
    if not result["evaluated_fights"]:raise SystemExit("no eligible holdout fights")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
