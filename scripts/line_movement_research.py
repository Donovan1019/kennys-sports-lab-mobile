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
        consensus.append({"event_id":event,"home":series[0]["home"],"away":series[0]["away"],"event_start":series[0]["event_start"],"bookmakers":len(values),"median_change_pp":median(values),"home_support":sum(v>0 for v in values),"away_support":sum(v<0 for v in values),"prediction":None})
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
        Path(f"feed/{sport}_line_movement.json").write_text(json.dumps(report,indent=2)+"\n")
        print(sport,"multi-snapshot bookmaker series:",report["paired_bookmaker_series"])
if __name__=="__main__":main()
