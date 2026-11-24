"""Leakage-safe line movement research from archived sportsbook quotes.

Compares earliest and latest captured snapshots per event/bookmaker; never
labels a quote 'closing' without verified pregame event start timestamps.
"""
import json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from statistics import median

def parse(value):
    try:
        t=datetime.fromisoformat(value.replace("Z","+00:00"))
        return t if t.tzinfo else None
    except (TypeError,ValueError,AttributeError):return None

def movement(archive, ledger=None, now=None):
    now = now or datetime.now(timezone.utc)
    starts=defaultdict(set)
    for r in (ledger or {}).get('baselines',[]):
        start,forecast,quote=(parse(r.get(k)) for k in ('event_start','forecast_at','quote_at'))
        if r.get('status')=='verified_pregame_quote' and all((start,forecast,quote)) and quote<=forecast<start and forecast<=now:
            starts[r.get('event_id')].add(start)
    rejected=0
    groups=defaultdict(list)
    for r in archive.get("quotes",[]):
        stamp=parse(r.get("captured_at"))
        p=r.get("home_no_vig")
        known=starts.get(r.get("event_id"),set())
        if len(known)!=1 or not stamp or stamp>=next(iter(known)) or stamp>now:
            rejected+=1
            continue
        if not stamp or type(p) not in (int,float) or not 0<p<1:continue
        if not all(r.get(k) for k in ("event_id","bookmaker","home","away")):continue
        groups[(r["event_id"],r["bookmaker"],r["away"],r["home"])].append((stamp,p))
    changes=[]
    for (event,book,away,home),rows in groups.items():
        rows.sort()
        if len({t for t,_ in rows}) != len(set(rows)):
            rejected+=1
            continue
        rows=sorted(set(rows))
        if len({t for t,_ in rows})<2:continue
        first,last=rows[0],rows[-1]
        delta=last[1]-first[1]
        steps=[b[1]-a[1] for a,b in zip(rows,rows[1:]) if a[1]!=b[1]]
        changes.append({"event_id":event,"bookmaker":book,"away":away,"home":home,"first_captured_at":first[0].isoformat(),"latest_captured_at":last[0].isoformat(),"first_home_no_vig":first[1],"latest_home_no_vig":last[1],"home_probability_change_pp":round(100*(last[1]-first[1]),3),"event_start":next(iter(starts[event])).isoformat(),"observations":len(rows),"direction":"home" if delta>0 else "away" if delta<0 else "flat","reversals":sum(a*b<0 for a,b in zip(steps,steps[1:])),"minutes_before_start":round((next(iter(starts[event]))-last[0]).total_seconds()/60,2),"is_verified_closing_line":False})
    events=defaultdict(list)
    for row in changes:events[row["event_id"]].append(row)
    consensus=[]
    for event, series in events.items():
        if len({r["bookmaker"] for r in series})!=len(series) or len({(r["home"],r["away"]) for r in series})!=1:continue
        values=[r["home_probability_change_pp"] for r in series]
        consensus.append({"event_id":event,"home":series[0]["home"],"away":series[0]["away"],"event_start":series[0]["event_start"],"bookmakers":len(values),"median_change_pp":median(values),"first_home_probability":median(r["first_home_no_vig"] for r in series),"latest_home_probability":median(r["latest_home_no_vig"] for r in series),"home_support":sum(v>0 for v in values),"away_support":sum(v<0 for v in values),"prediction":None})
    return {"event_consensus":consensus,"status":"research_only_not_closing_line_value","rejected_unverified_or_conflicting":rejected,"paired_bookmaker_series":len(changes),"series":sorted(changes,key=lambda x:(-abs(x["home_probability_change_pp"]),x["event_id"],x["bookmaker"]))}

def settle(report, games):
    from scripts.three_sport_backtest import normalize_team
    for row in report["event_consensus"]:
        start=parse(row["event_start"])
        matches=[g for g in games if g.get("completed") is True and parse(g.get("commence_time")) and abs((parse(g["commence_time"])-start).total_seconds())<=7200 and normalize_team(g.get("home"))==normalize_team(row["home"]) and normalize_team(g.get("away"))==normalize_team(row["away"])]
        unique={(str(g.get("event_id")),g.get("home_score"),g.get("away_score")) for g in matches}
        row["outcome"]=None
        if len(unique)==1:
            _,h,a=next(iter(unique))
            if type(h) is int and type(a) is int:
                row["outcome"]="home" if h>a else "away" if a>h else "push"
        d=row["median_change_pp"]
        row["movement_correct"]=None if not d or row["outcome"] not in ("home","away") else row["outcome"]==("home" if d>0 else "away")
    graded=[r for r in report["event_consensus"] if r["movement_correct"] is not None]
    report["outcome_audit"]={"graded_events":len(graded),"correct":sum(r["movement_correct"] for r in graded),"hit_rate":sum(r["movement_correct"] for r in graded)/len(graded) if graded else None,"status":"descriptive_not_out_of_sample"}

def benchmark(report):
    import math
    rows=sorted((r for r in report["event_consensus"] if r.get("outcome") in ("home","away")),key=lambda r:r["event_start"])
    if len(rows)<100:
        report["predictive_benchmark"]={"status":"UNAVAILABLE","reason":"At least 100 settled events required","settled_events":len(rows)}
        return
    split=rows[int(len(rows)*.7)]["event_start"]
    train=[r for r in rows if r["event_start"]<split]
    test=[r for r in rows if r["event_start"]>=split]
    if len(train)<50 or len(test)<30:
        report["predictive_benchmark"]={"status":"UNAVAILABLE","reason":"Insufficient chronological partition"}
        return
    def prob(r,b):
        p=r["latest_home_probability"]
        z=math.log(p/(1-p))+b*r["median_change_pp"]/100
        return 1/(1+math.exp(-max(-30,min(30,z))))
    def score(rs,b):
        return sum((prob(r,b)-(r["outcome"]=="home"))**2 for r in rs)/len(rs)
    b=min((i/4 for i in range(-16,17)),key=lambda x:score(train,x))
    report["predictive_benchmark"]={"status":"RESEARCH_ONLY","train_events":len(train),"holdout_events":len(test),"holdout_start":split,"movement_coefficient":b,"market_brier":score(test,0),"movement_brier":score(test,b),"first_observed_brier":sum((r["first_home_probability"]-(r["outcome"]=="home"))**2 for r in test)/len(test),"bet_eligible":False}

def enrich(report, core, forecasts):
    import random
    groups=defaultdict(list)
    for q in core.get("quotes",[]):
        t,s=parse(q.get("captured_at")),parse(q.get("event_start"))
        if t and s and t<s and t<=datetime.now(timezone.utc):
            groups[(q["event_id"],q["bookmaker"],q["market"],q["home"],q["away"],s)].append(q)
    report["core_market_movements"]=[]
    for (eid,book,market,home,away,start),rs in groups.items():
        if market not in ("spreads","totals"):continue
        rs.sort(key=lambda q:parse(q["captured_at"]))
        if len({q["captured_at"] for q in rs})<2:continue
        if any(len({(q["point"],q["home_no_vig"]) for q in rs if q["captured_at"]==t})>1 for t in {q["captured_at"] for q in rs}):continue
        a,b=rs[0],rs[-1]
        report["core_market_movements"].append(dict(event_id=eid,bookmaker=book,market=market,home=home,away=away,event_start=start.isoformat(),first_point=a["point"],latest_point=b["point"],point_change=b["point"]-a["point"],first_captured_at=a["captured_at"],latest_captured_at=b["captured_at"]))
    matched=[]
    for r in report["event_consensus"]:
        cutoff=min(parse(q["latest_captured_at"]) for q in report["series"] if q["event_id"]==r["event_id"])
        fs=[f for f in forecasts.get("forecasts",[]) if f.get("event_id")==r["event_id"] and f.get("home")==r["home"] and f.get("away")==r["away"] and parse(f.get("event_start"))==parse(r["event_start"]) and parse(f.get("forecast_at")) and parse(f["forecast_at"])<=cutoff and type(f.get("home_probability")) in (int,float) and 0<f["home_probability"]<1]
        if not fs:continue
        p=max(fs,key=lambda f:parse(f["forecast_at"]))["home_probability"]
        r["independent_research_probability"]=p
        rng=random.Random(r["event_id"])
        n=10000
        r["independent_monte_carlo"]={"trials":n,"home_fraction":sum(rng.random()<p for _ in range(n))/n,"status":"RESEARCH_ONLY_BERNOULLI_NOT_SCORE_SIMULATION"}
        if r.get("outcome") in ("home","away"):matched.append(r)
    report["independent_comparison"]={"status":"DESCRIPTIVE_ONLY" if matched else "UNAVAILABLE","matched_settled_events":len(matched),"independent_brier":sum((r["independent_research_probability"]-(r["outcome"]=="home"))**2 for r in matched)/len(matched) if matched else None,"market_brier":sum((r["latest_home_probability"]-(r["outcome"]=="home"))**2 for r in matched)/len(matched) if matched else None}

def combined_benchmark(report):
    rows=sorted([r for r in report["event_consensus"] if r.get("outcome") in ("home","away") and r.get("score_simulation",{}).get("trials") and r["score_simulation"].get("tie_probability")==0],key=lambda r:r["event_start"])
    if len(rows)<100:
        report["combined_benchmark"]={"status":"UNAVAILABLE","matched_events":len(rows),"reason":"100 settled independent score simulations required"}
        return
    split=rows[int(.7*len(rows))]["event_start"]
    train=[r for r in rows if r["event_start"]<split]
    test=[r for r in rows if r["event_start"]>=split]
    if len(train)<50 or len(test)<30:
        report["combined_benchmark"]={"status":"UNAVAILABLE","reason":"Insufficient chronological partition"}
        return
    def p(r,w,b):
        return max(.001,min(.999,w*r["score_simulation"]["home_win_probability"]+(1-w)*r["latest_home_probability"]+b*r["median_change_pp"]/100))
    def score(rs,w,b):
        return sum((p(r,w,b)-(r["outcome"]=="home"))**2 for r in rs)/len(rs)
    w,b=min(((i/10,j/4) for i in range(11) for j in range(-8,9)),key=lambda x:score(train,*x))
    report["combined_benchmark"]={"status":"RESEARCH_ONLY","train_events":len(train),"holdout_events":len(test),"independent_weight":w,"movement_coefficient":b,"combined_brier":score(test,w,b),"market_brier":score(test,0,0),"independent_brier":score(test,1,0),"bet_eligible":False}

def main():
    for src in sorted(Path("feed").glob("*_paired_moneyline_archive.json")):
        sport=src.name.removesuffix("_paired_moneyline_archive.json")
        src=Path(f"feed/{sport}_paired_moneyline_archive.json")
        if not src.exists():continue
        ledger=Path(f"feed/{sport}_market_baseline_ledger.json")
        report=movement(json.loads(src.read_text()),json.loads(ledger.read_text()) if ledger.exists() else {})
        games=[]
        league=sport.rsplit("_",1)[-1]
        for result in Path("backtests/results").glob(f"*/{league}.json"):
            games.extend(json.loads(result.read_text()).get("games",[]))
        settle(report,games)
        from scripts.line_movement_simulation import simulate
        for row in report["event_consensus"]:
            cutoff=min(parse(q["latest_captured_at"]) for q in report["series"] if q["event_id"]==row["event_id"])
            row["score_simulation"]=simulate(sport,row,games,cutoff)
        benchmark(report)
        combined_benchmark(report)
        core=Path(f"feed/{sport}_core_movement_archive.json")
        forecasts=Path(f"feed/{sport}_forecast_ledger.json")
        enrich(report,json.loads(core.read_text()) if core.exists() else {},json.loads(forecasts.read_text()) if forecasts.exists() else {})
        Path(f"feed/{sport}_line_movement.json").write_text(json.dumps(report,indent=2)+"\n")
        print(sport,"multi-snapshot bookmaker series:",report["paired_bookmaker_series"])
if __name__=="__main__":main()
