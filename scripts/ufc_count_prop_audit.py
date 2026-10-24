#!/usr/bin/env python3
"""Chronological UFC count-prop baseline audit; retrospective research only."""
import argparse,json,math
from collections import defaultdict
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join
from scripts.ufc_joined_chronological_rows import convert
from scripts.ufc_historical_prefix_features import build as historical_prefix

MARKETS={"sig_landed":"sig_landed","sig_attempted":"sig_attempted",
         "takedowns_landed":"takedowns_landed","takedowns_attempted":"takedowns_attempted"}
def poisson_tail(lam,k):
    if not math.isfinite(lam) or lam<0:return None
    if lam>600:
        z=(math.floor(k)+.5-lam)/math.sqrt(lam)
        return max(0,min(1,.5*math.erfc(z/math.sqrt(2))))
    term=math.exp(-lam); cdf=term
    for i in range(1,math.floor(k)+1):
        term*=lam/i;cdf+=term
    return max(0,min(1,1-cdf))
def audit(rows,min_prior=3):
    """Predictions use only completed earlier-date bouts for each fighter."""
    ordered=sorted(rows,key=lambda r:(r["fight_time"],r["fight_id"],r["fighter_id"]))
    prior=defaultdict(list);results=defaultdict(list);excluded=defaultdict(int)
    for day in sorted(set(r["fight_time"][:10] for r in ordered)):
        batch=[r for r in ordered if r["fight_time"][:10]==day]
        for row in batch:
            history=prior[row["fighter_id"]]
            if len(history)<min_prior:
                excluded["insufficient_prior_fights"]+=1;continue
            exposure=sum(float(h["active_seconds"]) for h in history)
            duration=float(row["active_seconds"])
            if exposure<=0 or duration<=0:
                excluded["invalid_exposure"]+=1;continue
            for name,key in MARKETS.items():
                count=float(row[key]);rate=sum(float(h[key]) for h in history)/exposure
                # Oracle-duration diagnostic: realized fight duration is NOT known pre-fight.
                # Isolates count dispersion and rate accuracy, not deployable prop performance.
                lam=rate*duration
                if not 0<=lam<=10000:continue
                threshold=math.floor(lam)+.5
                prob=poisson_tail(lam,threshold)
                hit=int(count>threshold)
                results[name].append((lam,count,prob,hit,row["fight_id"],day))
        for row in batch:
            if str(row["settled"]).lower()=="true":prior[row["fighter_id"]].append(row)
    output={}
    for market,values in results.items():
        n=len(values)
        if not n:continue
        mean_error=sum(p-y for p,y,*_ in values)/n
        mae=sum(abs(p-y) for p,y,*_ in values)/n
        brier=sum((p-y)**2 for _,_,p,y,*_ in values)/n
        bins=[]
        for lo in range(0,10,2):
            subset=[v for v in values if lo/10<=v[2]<(lo+2)/10 or (lo==8 and v[2]==1)]
            if subset:bins.append({"predicted_range":[lo/10,(lo+2)/10],"n":len(subset),
                "mean_predicted":sum(v[2] for v in subset)/len(subset),
                "observed":sum(v[3] for v in subset)/len(subset)})
        output[market]={"n":n,"mae":mae,"mean_error":mean_error,"brier":brier,
            "calibration_bins":bins,"distinct_fights":len(set(v[4] for v in values))}
    return {"schema":1,"method":"PRIOR-DATE FIGHTER RATE + ORACLE DURATION POISSON",
        "point_in_time_certified":False,"bet_eligible":False,
        "predictive_duration_available":False,"model_validated_for_betting":False,
        "limitations":"Retrospective source capture times unverified; realized fight duration used solely to isolate count-rate/dispersion errors. Not a true pre-fight backtest or betting edge.",
        "markets":output,"excluded":dict(excluded)}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv");wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    if linked["status"]!="JOINED":raise SystemExit("Fight identity join failed")
    converted=convert(linked["records"])
    report=audit(converted["rows"])
    if not report["markets"]:raise SystemExit("No valid historical count market observations")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v["n"] for k,v in report["markets"].items()}))
if __name__=="__main__":main()
