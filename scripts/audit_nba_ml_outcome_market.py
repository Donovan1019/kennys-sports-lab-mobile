#!/usr/bin/env python3
"""Research-only NBA odds/outcome joins and near-tipoff CLV evidence."""
import datetime as dt
import json
import pathlib
from collections import defaultdict
from scripts.audit_nba_ml_market_evidence import parse_time

ARCHIVES=pathlib.Path("data/nba_ml_odds_archive")
GAMES=pathlib.Path("data/nba_ml_historical_games.json")
OUT=pathlib.Path("feed/nba_ml_outcome_market_audit.json")

def implied(price):
    if not isinstance(price,(int,float)) or isinstance(price,bool) or price==0 or -100<price<100:raise ValueError("Invalid American odds")
    return (-price)/(-price+100) if price<0 else 100/(price+100)

def evaluate(archives, games):
    by_event=defaultdict(list)
    for archive in archives:
        if archive.get("status")!="ok":continue
        captured=parse_time(archive.get("captured_at"))
        if not captured:continue
        for r in archive.get("rows",[]):
            tip=parse_time(r.get("commence_time"));updated=parse_time(r.get("quote_updated_at"))
            if not tip or not updated or not updated<=captured<tip:continue
            try:prob=implied(r.get("price"))
            except ValueError:continue
            if not isinstance(r.get("selection"),str) or not isinstance(r.get("bookmaker"),str):continue
            by_event[(r.get("event"),r["bookmaker"],r["selection"])].append((captured,tip,prob,r))
    results={}
    for g in games:
        if not all(k in g for k in ("home","away","home_win","date")):continue
        tip=parse_time(g["date"])
        if not tip:continue
        for team in (g["home"],g["away"]):
            event=f'{g["away"]} @ {g["home"]}'
            for (label,book,selection),values in by_event.items():
                if label!=event or selection!=team:continue
                valid=sorted((v for v in values if v[1]==tip),key=lambda v:v[0])
                if not valid:continue
                first=valid[0];close_candidates=[v for v in valid if 0<=(tip-v[0]).total_seconds()<=900]
                key=(str(g.get("id","")),book,team)
                if key in results:continue
                won=int(bool(g["home_win"])) if team==g["home"] else 1-int(bool(g["home_win"]))
                row={"event_id":g.get("id"),"book":book,"selection":team,"won":won,
                     "opening_reference_implied":round(first[2],6),
                     "opening_reference_brier":round((first[2]-won)**2,6),
                     "snapshots":len({v[0] for v in valid}),
                     "verified_near_tipoff_quote":bool(close_candidates)}
                if close_candidates:
                    closing=close_candidates[-1]
                    row["near_tipoff_reference_implied"]=round(closing[2],6)
                    row["reference_implied_probability_movement"]=round(closing[2]-first[2],6)
                results[key]=row
    rows=list(results.values())
    paired=[r for r in rows if r["verified_near_tipoff_quote"] and r["snapshots"]>=2]
    return {"status":"research_only","joined_selection_rows":len(rows),
            "unique_joined_events":len({r["event_id"] for r in rows}),
            "mean_reference_brier":round(sum(r["opening_reference_brier"] for r in rows)/len(rows),6) if rows else None,
            "near_tipoff_paired_rows":len(paired),
            "historical_pregame_odds_backtest_verified":False,"closing_line_value_verified":False,
            "warning":"Market reference odds are not executed bets; near-tipoff quotes are not official closing lines. Selection-time model provenance, Onyx prices, and independently verified outcomes are required before betting promotion.",
            "sample_rows":rows[:25]}

def main():
    archives=[]
    for p in sorted(ARCHIVES.glob("*/*.json")):
        try:archives.append(json.loads(p.read_text()))
        except (OSError,ValueError):continue
    try:cache=json.loads(GAMES.read_text());games=[g for day in cache.get("days",{}).values() for g in day]
    except (OSError,ValueError):games=[]
    report=evaluate(archives,games)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print("NBA outcome/market audit:",report["joined_selection_rows"],"rows,",report["near_tipoff_paired_rows"],"near-tipoff pairs")
if __name__=="__main__":main()
