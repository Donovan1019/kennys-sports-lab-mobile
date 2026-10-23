#!/usr/bin/env python3
"""UFC no-vig and EV audit; no bet approval without independently validated probabilities."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path

def implied(american):
    if isinstance(american,bool) or not isinstance(american,int) or -100<american<100:
        raise ValueError("American odds must be integer <= -100 or >= +100")
    return 100/(american+100) if american>0 else -american/(-american+100)

def profit_per_unit(american):
    return american/100 if american>0 else 100/(-american)

def parse_time(s):
    x=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
    if x.tzinfo is None:
        raise ValueError("Timezone-aware quote required")
    return x.astimezone(dt.timezone.utc)

def evaluate(market,model,now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    if market.get("market")!="moneyline":
        raise ValueError("Only two-sided moneyline supported")
    if not market.get("fight_id") or market.get("fight_id")!=model.get("fight_id"):
        raise ValueError("Fight identity mismatch")
    start=parse_time(market["start_time"])
    quoted=parse_time(market["quoted_at"])
    if quoted>now or quoted>=start or (now-quoted).total_seconds()>900:
        raise ValueError("Quote stale, future-dated or after fight start")
    if start<=now:
        raise ValueError("Fight already started")
    red=market["red_odds"]
    blue=market["blue_odds"]
    pr,pb=implied(red),implied(blue)
    overround=pr+pb
    if not 1<=overround<=1.25:
        raise ValueError("Invalid two-sided book overround")
    probability=model.get("red_win_probability")
    if isinstance(probability,bool) or not isinstance(probability,(int,float)) or not math.isfinite(probability) or not 0<probability<1:
        raise ValueError("Invalid model probability")
    sides={}
    for name,odds,p,market_p in (("red",red,probability,pr),("blue",blue,1-probability,pb)):
        ev=p*profit_per_unit(odds)-(1-p)
        sides[name]={"american_odds":odds,"book_implied":market_p,"no_vig":market_p/overround,
                     "model_probability":p,"ev_per_unit":ev,"fair_american":round(100*(1-p)/p) if p<=.5 else round(-100*p/(1-p))}
    validated=model.get("independent_holdout_passed") is True and model.get("calibrated") is True
    return {"fight_id":market["fight_id"],"market":"moneyline","quoted_at":quoted.isoformat(),
            "source":market.get("source") or "unverified","overround":overround,"sides":sides,
            "research_only":True,"bet_eligible":False,"model_validated":validated,
            "blockers":["No verified model calibration/independent holdout" ] if not validated else
                       ["Manual betting approval and verified sportsbook availability required"],
            "note":"EV calculations are conditional on input probabilities; positive EV is not evidence of a proven edge."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--market",required=True)
    p.add_argument("--model",required=True)
    p.add_argument("--output",default="backtests/reports/ufc_moneyline_ev.json")
    a=p.parse_args()
    market=json.loads(Path(a.market).read_text())
    model=json.loads(Path(a.model).read_text())
    report=evaluate(market,model)
    out=Path(a.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print("UFC moneyline audit generated; bet eligibility remains false")
if __name__=="__main__":main()
