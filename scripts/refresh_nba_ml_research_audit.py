#!/usr/bin/env python3
"""Research-only NBA moneyline Monte Carlo audit from matching current feeds."""
import datetime as dt, json, pathlib, random, math
NOW=dt.datetime.now(dt.timezone.utc)
def parse(v):
    return dt.datetime.fromisoformat(v.replace("Z","+00:00"))
def main():
    odds=json.loads(pathlib.Path("feed/basketball_nba.json").read_text())
    model=json.loads(pathlib.Path("feed/nba_ml_predictions.json").read_text())
    result={"status":"unavailable","generated_at":NOW.isoformat(),"draws":10000,"games":[],"parlays":[],"reason":""}
    try:
        if odds.get("status")!="ok" or model.get("status")!="validated" or model.get("calibration_passed") is not True:raise ValueError("Odds or independent model unavailable")
        if abs((parse(odds["fetched_at"])-parse(model["generated_at"])).total_seconds())>600:raise ValueError("Odds and model snapshot timestamps do not match")
        if (NOW-parse(odds["fetched_at"])).total_seconds()>9000:raise ValueError("Odds snapshot stale")
        preds={(str(p["event_id"]),p["team"]):p["win_probability"] for p in model.get("predictions",[])}
        bybook={}
        for r in odds.get("odds",[]):
            if r.get("market")!="h2h" or not r.get("event_id") or not r.get("bookmaker"):continue
            try:
                if parse(r["commence_time"])<=NOW or (NOW-parse(r["updated_at"])).total_seconds()>9000:continue
                price=float(r["price"])
                if price==0 or not math.isfinite(price):continue
            except (ValueError,TypeError,KeyError):continue
            bybook.setdefault((str(r["event_id"]),r["bookmaker"]),[]).append(r)
        rng=random.Random(20261109)
        for (eid,book),rs in bybook.items():
            if len(rs)!=2 or len({r["selection"] for r in rs})!=2:continue
            for r in rs:
                team=r["selection"];p=preds.get((eid,team))
                if not isinstance(p,(int,float)) or not 0<p<1:continue
                price=float(r["price"]);decimal=1+100/(-price) if price<0 else 1+price/100
                mc=sum(rng.random()<p for _ in range(10000))/10000
                result["games"].append({"event_id":eid,"bookmaker":book,"team":team,"price":price,"model_probability":p,"mc_probability":mc,"single_leg_ev":p*decimal-1,"stress_ev_minus_3pp":max(0,p-.03)*decimal-1,"market_divergence_flag":False})
        # Independent-game research combinations; never imply executable sportsbook pricing.
        books=sorted({g["bookmaker"] for g in result["games"]})
        for book in books:
            candidates=sorted((g for g in result["games"] if g["bookmaker"]==book and g["price"]<0 and g["model_probability"]>=.60 and g["stress_ev_minus_3pp"]>0),key=lambda g:g["stress_ev_minus_3pp"],reverse=True)
            unique=[];seen=set()
            for g in candidates:
                if g["event_id"] not in seen:unique.append(g);seen.add(g["event_id"])
            for n in (2,3,4,5):
                if len(unique)<n:continue
                legs=unique[:n];joint=math.prod(g["model_probability"] for g in legs)
                stress=math.prod(max(0,g["model_probability"]-.03) for g in legs)
                result["parlays"].append({"bookmaker":book,"legs":[{"event_id":g["event_id"],"team":g["team"]} for g in legs],"independent_mc_probability":sum(all(rng.random()<g["model_probability"] for g in legs) for _ in range(10000))/10000,"stress_probability_minus_3pp":stress,"betting_eligible":False,"executable_parlay_quote_verified":False})
        result["status"]="simulated_not_bet_eligible" if result["games"] else "unavailable"
        result["reason"]="Independent-game research simulations only; lineup, correlation, executable parlay quote and CLV unverified"
    except (ValueError,KeyError,TypeError) as e:result["reason"]=str(e)
    pathlib.Path("feed/nba_ml_simulation_audit.json").write_text(json.dumps(result,indent=2)+"\n")
    print("NBA ML simulation audit:",result["status"],len(result["games"]),"game sides; parlays",len(result["parlays"]))
if __name__=="__main__":main()
