#!/usr/bin/env python3
"""Deterministic UFC research simulator. Explicitly uncalibrated, never bet eligible."""
import hashlib
import json
import math
import random
from pathlib import Path

def validate(f):
    required=("id","red","blue","start_time")
    if not isinstance(f,dict) or any(not f.get(k) for k in required):
        raise ValueError("Fight identity incomplete")
    for side in ("red","blue"):
        stats=f.get(side+"_stats")
        if not isinstance(stats,dict):
            raise ValueError("Missing fighter stats: "+side)
        for key in ("ko_rate","submission_rate","decision_rate"):
            value=stats.get(key)
            if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or not 0<=value<=1:
                raise ValueError("Invalid "+side+" "+key)
        if abs(sum(stats[k] for k in ("ko_rate","submission_rate","decision_rate"))-1)>0.01:
            raise ValueError("Method rates must sum to one")
        if not isinstance(stats.get("sample_size"),int) or stats["sample_size"]<10:
            raise ValueError("Insufficient verified fighter sample")
    if f.get("scheduled_rounds") not in (3,5):
        raise ValueError("Unverified scheduled rounds")
    if f.get("stats_verified") is not True or f.get("fighter_status_verified") is not True:
        raise ValueError("Fighter inputs unverified")

def simulate(f,n=20000):
    validate(f)
    if not isinstance(n,int) or not 1000<=n<=200000:
        raise ValueError("Invalid simulation count")
    seed=int.from_bytes(hashlib.sha256(json.dumps(f,sort_keys=True).encode()).digest()[:8],"big")
    rng=random.Random(seed)
    wins={"red":0,"blue":0}
    methods={"KO/TKO":0,"Submission":0,"Decision":0}
    rounds={str(k):0 for k in range(1,f["scheduled_rounds"]+1)}
    for _ in range(n):
        # Neutral 50/50 winner until an opponent-adjusted skill model is calibrated.
        winner="red" if rng.random()<0.5 else "blue"
        wins[winner]+=1
        stats=f[winner+"_stats"]
        draw=rng.random()
        method="KO/TKO" if draw<stats["ko_rate"] else ("Submission" if draw<stats["ko_rate"]+stats["submission_rate"] else "Decision")
        methods[method]+=1
        round_no=f["scheduled_rounds"] if method=="Decision" else rng.randint(1,f["scheduled_rounds"])
        rounds[str(round_no)]+=1
    return {"fight_id":f["id"],"iterations":n,"seed":seed,"winner_probability":{k:v/n for k,v in wins.items()},
            "method_probability":{k:v/n for k,v in methods.items()},
            "ending_round_probability":{k:v/n for k,v in rounds.items()},
            "model_status":"UNCALIBRATED_RESEARCH_ONLY","bet_eligible":False,
            "limitations":["Neutral 50/50 winner prior; no opponent-adjusted fighter strength",
                           "Finish rounds modeled uniformly; not an empirical hazard curve",
                           "Fighter historical method mix is not a matchup prediction",
                           "Not suitable for EV, Diamond Plays or betting recommendations"]}

def export(input_path="feed/ufc_research.json",output_path="feed/ufc_simulations.json"):
    feed=json.loads(Path(input_path).read_text())
    results=[]
    blocked=[]
    for f in feed.get("fights",[]):
        try: results.append(simulate(f))
        except (ValueError,TypeError,KeyError) as exc: blocked.append({"fight_id":f.get("id"),"reason":str(exc)})
    payload={"sport":"UFC","schema":1,"research_only":True,"bet_eligible":False,
             "simulations":results,"blocked":blocked}
    out=Path(output_path)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2)+"\n")
    return payload

if __name__=="__main__":
    payload=export()
    print(f"UFC research simulations: {len(payload['simulations'])}; blocked: {len(payload['blocked'])}")
