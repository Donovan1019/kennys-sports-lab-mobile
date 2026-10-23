#!/usr/bin/env python3
"""Free UFC odds entry: user-observed DK/FD moneylines, no paid API.

Requires explicit capture timestamp and both fighters' prices. All entries
remain research-only until independent verification and calibration.
"""
import argparse
import json
from pathlib import Path
from scripts.ufc_odds_connector import normalize, parse_time

BOOKS={"draftkings":"DraftKings","fanduel":"FanDuel"}

def build(entries, captured_at_utc):
    capture=parse_time(captured_at_utc)
    snapshots={}
    for key,display in BOOKS.items():
        snapshots[key]={"schema":1,"sport":"UFC","source":"user_entered_free_odds",
                        "source_authorized":True,"captured_at_utc":captured_at_utc,
                        "moneylines":[]}
    for row in entries:
        book=row.get("book","").lower()
        if book not in BOOKS:
            raise ValueError("Only DraftKings and FanDuel are supported")
        for field in ("event_id","fighter","opponent","fighter_odds","opponent_odds","event_start_utc"):
            if field not in row:
                raise ValueError("Missing "+field)
        if parse_time(row["event_start_utc"])<=capture:
            raise ValueError("Event must start after quote capture")
        item={field:row[field] for field in ("event_id","fighter","opponent",
               "fighter_odds","opponent_odds","event_start_utc")}
        item.update({"sportsbook":BOOKS[book],"source_verified":False,
                     "fighters_verified":False,"model_calibrated":False,
                     "odds_executable":False})
        snapshots[book]["moneylines"].append(item)
    for key in BOOKS:
        normalize(snapshots[key])
    return snapshots

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,help="Local JSON: captured_at_utc and entries")
    p.add_argument("--output-dir",required=True)
    args=p.parse_args()
    raw=json.loads(Path(args.input).read_text())
    result=build(raw["entries"],raw["captured_at_utc"])
    folder=Path(args.output_dir)
    folder.mkdir(parents=True,exist_ok=True)
    for key,data in result.items():
        (folder/(key+".json")).write_text(json.dumps(data,indent=2)+"\n")
        print(key,len(data["moneylines"]),"unverified user-entered quotes")
if __name__=="__main__":main()
