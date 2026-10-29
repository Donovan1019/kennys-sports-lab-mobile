#!/usr/bin/env python3
"""Audit available pregame quote coverage without inventing CLV, results, or prices."""
import datetime as dt
import json
import pathlib
from collections import defaultdict

ROOT=pathlib.Path("data/nba_ml_odds_archive")
OUT=pathlib.Path("feed/nba_ml_market_evidence.json")

def parse_time(value):
    try:
        t=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
        return t if t.tzinfo is not None else None
    except (ValueError,TypeError,AttributeError):
        return None

def audit_archives(archives):
    quotes=defaultdict(list)
    invalid=0
    for archive in archives:
        if archive.get("status")!="ok":continue
        captured=parse_time(archive.get("captured_at"))
        for row in archive.get("rows",[]):
            tip=parse_time(row.get("commence_time"))
            updated=parse_time(row.get("quote_updated_at"))
            price=row.get("price")
            if not captured or not tip or captured>=tip or not updated or updated>captured or updated>=tip or not isinstance(price,(int,float)) or isinstance(price,bool) or price==0 or -100<price<100:
                invalid+=1
                continue
            key=(str(row.get("event_id","")),str(row.get("bookmaker","")),str(row.get("selection","")))
            if not all(key):invalid+=1;continue
            quotes[key].append((captured,updated,price))
    paired=0;early_only=0
    for values in quotes.values():
        # A close is a separate, verified pre-tipoff snapshot no more than 15 minutes before tipoff.
        # Tipoff metadata is deliberately not retained in this aggregate: no CLV can be asserted.
        if len({v[0] for v in values})>=2:paired+=1
        else:early_only+=1
    return {"status":"research_only","valid_quote_keys":len(quotes),"keys_with_multiple_snapshots":paired,
            "keys_with_one_snapshot":early_only,"rejected_rows":invalid,
            "historical_pregame_odds_backtest_verified":False,
            "closing_line_value_verified":False,
            "reason":"Coverage counts are not a backtest. No verified closing quote, outcome join, execution odds or precommitted bet selection is established."}

def main():
    files=sorted(ROOT.glob("*/*.json")) if ROOT.exists() else []
    archives=[]
    for path in files:
        try:archives.append(json.loads(path.read_text()))
        except (OSError,ValueError):continue
    report=audit_archives(archives)
    report["archive_files_scanned"]=len(files)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print("NBA ML market evidence:",report)
if __name__=="__main__":main()
