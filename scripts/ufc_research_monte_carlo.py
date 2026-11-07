#!/usr/bin/env python3
"""Reproducible UFC hypothetical winner Monte Carlo; NOT a validated fight model."""
import json,random,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(fights,draws=10000):
    result=[]
    for f in fights:
        p=f.get("sparse_data_probability") or {}
        center=p.get("red")
        interval=p.get("red_uncertainty_interval") or []
        if not isinstance(center,(int,float)) or len(interval)!=2 or not all(isinstance(x,(int,float)) for x in interval):
            result.append({"fight_id":f["fight_id"],"red":f["red"],"blue":f["blue"],"status":"UNAVAILABLE","reason":"No existing research probability and uncertainty interval"});continue
        lo,hi=interval
        if not 0<=lo<=center<=hi<=1:
            result.append({"fight_id":f["fight_id"],"red":f["red"],"blue":f["blue"],"status":"UNAVAILABLE","reason":"Invalid uncertainty inputs"});continue
        # Triangular uncertainty distribution: mode is the existing sparse research estimate.
        rng=random.Random(str(f["fight_id"])+":ufc-research-v1")
        wins=0
        for _ in range(draws):
            scenario_p=rng.triangular(lo,hi,center)
            wins+=rng.random()<scenario_p
        result.append({"fight_id":f["fight_id"],"red":f["red"],"blue":f["blue"],"status":"HYPOTHETICAL_RESEARCH_ONLY","trials":draws,"red_scenario_win_fraction":round(wins/draws,4),"blue_scenario_win_fraction":round(1-wins/draws,4),"red_input_probability":center,"red_input_uncertainty_interval":[lo,hi],"scenario_distribution":"triangular around uncalibrated sparse-data probability","bet_eligible":False,"model_ev":None,"limitations":["Not calibrated or backtested; results are NOT predictive win probabilities","Fighter identity, injury, lineup and scheduled rounds not verified","This is an uncertainty scenario, not a round-by-round fight simulator"]})
    return result
def main():
    src=json.loads((ROOT/"feed/ufc_joined_stats.json").read_text())
    rows=run(src["fights"])
    out={"schema":"ufc-hypothetical-monte-carlo-v1","sport":"UFC","research_only":True,"bet_eligible":False,"trials_per_fight":10000,"scenario_count":sum(x["status"]=="HYPOTHETICAL_RESEARCH_ONLY" for x in rows),"validated_full_fight_simulations":0,"fights":rows}
    (ROOT/"feed/ufc_research_monte_carlo.json").write_text(json.dumps(out,indent=2)+"\n")
    print("Hypothetical UFC Monte Carlo scenarios:",out["scenario_count"])
if __name__=="__main__":main()
