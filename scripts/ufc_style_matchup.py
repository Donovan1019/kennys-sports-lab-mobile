#!/usr/bin/env python3
"""UFC style matchup diagnostics; descriptive and non-predictive until calibrated."""
import argparse
import json
import math
from pathlib import Path

FIELDS=("sig_strikes_landed_per_min","sig_strikes_absorbed_per_min","sig_strike_accuracy",
        "sig_strike_defense","takedowns_per_15","takedown_accuracy","takedown_defense",
        "submission_attempts_per_15")
RATE_FIELDS=("sig_strike_accuracy","sig_strike_defense","takedown_accuracy","takedown_defense")

def validate(f):
    if not isinstance(f,dict) or not isinstance(f.get("name"),str) or not f["name"].strip():
        raise ValueError("Fighter identity missing")
    if f.get("stats_verified") is not True:
        raise ValueError("Fighter stats not verified")
    minutes=f.get("observed_minutes")
    if isinstance(minutes,bool) or not isinstance(minutes,(int,float)) or not math.isfinite(minutes) or minutes<45:
        raise ValueError("Insufficient verified fight time")
    for key in FIELDS:
        value=f.get(key)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            raise ValueError("Missing or invalid "+key)
        if key in RATE_FIELDS and value>1:
            raise ValueError("Percentage must be fraction in [0,1]")

def matchup(red,blue):
    validate(red);validate(blue)
    if red["name"]==blue["name"]:
        raise ValueError("Same fighter on both sides")
    def indicators(a,b):
        return {"striking_volume_differential_per_min":a["sig_strikes_landed_per_min"]-b["sig_strikes_absorbed_per_min"],
                "striking_defense_advantage":a["sig_strike_defense"]-b["sig_strike_accuracy"],
                "takedown_attack_vs_defense":a["takedown_accuracy"]*(1-b["takedown_defense"]),
                "takedown_activity_per_15":a["takedowns_per_15"],
                "submission_activity_per_15":a["submission_attempts_per_15"]}
    return {"red":red["name"],"blue":blue["name"],
            "red_indicators":indicators(red,blue),"blue_indicators":indicators(blue,red),
            "research_only":True,"bet_eligible":False,"winner_probability":None,
            "limitations":["Aggregate career rates are not opponent-adjusted or recency-weighted",
                           "Takedown interaction is a heuristic, not a calibrated success probability",
                           "Weight class, stance, reach, age, injuries, short notice and fight pace are not modeled",
                           "No market odds, uncertainty intervals or verified performance edge"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--red",required=True)
    p.add_argument("--blue",required=True)
    p.add_argument("--output",default="backtests/reports/ufc_style_matchup.json")
    args=p.parse_args()
    report=matchup(json.loads(Path(args.red).read_text()),json.loads(Path(args.blue).read_text()))
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print("UFC style indicators generated; no betting prediction")
if __name__=="__main__":main()
