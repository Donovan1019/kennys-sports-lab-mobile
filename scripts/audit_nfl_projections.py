#!/usr/bin/env python3
"""Leakage-safe expanding-history audit of the *unadjusted* NFL projection baseline.

Requires at least 8 prior observed games. No matchup/roster assumptions are backtested.
Does not validate sportsbook EV or probabilities. Exit nonzero on insufficient sample
or material systematic bias; never report a betting-ready model from this audit alone.
"""
import json, math, statistics, sys
from collections import defaultdict
from pathlib import Path

MARKETS = {
 "Passing Yards":"Passing yards","Passing TDs":"Passing touchdowns",
 "Rushing Yards":"Rushing yards","Receiving Yards":"Receiving yards",
 "Receptions":"Receptions","Rushing TDs":"Rushing touchdowns",
 "Receiving TDs":"Receiving touchdowns",
}
ROLES={"Passing Yards":{"QB"},"Passing TDs":{"QB"},"Rushing Yards":{"QB","RB","WR"},
       "Receiving Yards":{"RB","WR","TE"},"Receptions":{"RB","WR","TE"},
       "Rushing TDs":{"QB","RB","WR"},"Receiving TDs":{"RB","WR","TE"}}
def predict(history):
    def mean(x):return sum(x)/len(x)
    return .25*mean(history[:5])+.50*mean(history[:10])+.25*mean(history[:17])
def audit(payload):
    errors=defaultdict(list)
    counts=defaultdict(set)
    for p in payload.get("players",[]):
        role=str(p.get("position","")).upper()
        games=sorted((g for g in p.get("games",[]) if g.get("season") is not None and g.get("week") is not None and g.get("season_type") in ("REG","POST")),
                     key=lambda g:(int(g["season"]),int(g["week"]),g["season_type"]=="POST"))
        for market,key in MARKETS.items():
            if role not in ROLES[market]:continue
            observed=[(g,float(g["values"][key])) for g in games if key in g.get("values",{}) and g["values"][key] is not None and math.isfinite(float(g["values"][key])) and float(g["values"][key])>=0]
            for idx in range(8,len(observed)):
                g,actual=observed[idx]
                if int(g["season"])!=2026:continue
                history=[v for _,v in reversed(observed[:idx])]
                forecast=predict(history)
                errors[market].append((forecast-actual,abs(forecast-actual),forecast,actual))
                counts[market].add(str(p.get("id") or p.get("name")))
    results={}
    for market in MARKETS:
        rows=errors[market]
        n=len(rows)
        if not n:
            results[market]={"samples":0,"players":0,"status":"INSUFFICIENT_DATA"}
            continue
        bias=statistics.mean(x[0] for x in rows)
        mae=statistics.mean(x[1] for x in rows)
        rmse=math.sqrt(statistics.mean(x[0]**2 for x in rows))
        avg_actual=statistics.mean(x[3] for x in rows)
        results[market]={"samples":n,"players":len(counts[market]),"bias":round(bias,3),"mae":round(mae,3),"rmse":round(rmse,3),"mean_actual":round(avg_actual,3),
                         "bias_pct_of_actual":round(100*bias/avg_actual,2) if avg_actual>0 else None,
                         "status":"REVIEW" if n<50 or abs(bias)>max(.1*avg_actual, .1) else "BASELINE_CHECK_PASS"}
    return {"scope":"2026 actuals; prior-game-only NFL historical baseline","limitations":["Not a calibrated probability model","No sportsbook closing-line comparison","No verified current roster/availability","NFL market baseline only; no matchup factor"],"markets":results}

def main():
    path=Path(sys.argv[1] if len(sys.argv)>1 else "feed/nfl_player_stats.json")
    report=Path(sys.argv[2] if len(sys.argv)>2 else "reports/nfl_projection_audit.json")
    result=audit(json.loads(path.read_text(encoding="utf-8")))
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    if not any(v["samples"]>=50 for v in result["markets"].values()):
        raise SystemExit("INSUFFICIENT_DATA: no NFL market has 50 backtest observations")
if __name__=="__main__":main()
