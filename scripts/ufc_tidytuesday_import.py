#!/usr/bin/env python3
"""Import a frozen public UFC CSV snapshot for research, never betting eligibility.

The TidyTuesday snapshot is historical, not a licensed live fighter-stats API.
This module keeps outcomes separate from pre-fight features and avoids
claiming that historical odds are timestamp-verified.
"""
import argparse
import csv
import datetime as dt
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2026/2026-07-07/"
FILES = ("ufc_fights.csv", "ultimate_ufc_dataset.csv")
FEATURES = ("r_wins", "b_wins", "r_losses", "b_losses",
            "r_avg_sig_str_landed", "b_avg_sig_str_landed",
            "r_avg_td_landed", "b_avg_td_landed",
            "r_avg_sub_att", "b_avg_sub_att", "r_age", "b_age",
            "r_reach_cms", "b_reach_cms", "r_height_cms", "b_height_cms")

def rows_from_text(text):
    return list(csv.DictReader(io.StringIO(text)))

def get_source(name, source_dir=None):
    if name not in FILES:
        raise ValueError("Unexpected UFC source filename")
    if source_dir:
        return (Path(source_dir) / name).read_text(encoding="utf-8-sig")
    with urlopen(Request(BASE + name, headers={"User-Agent":"KennysSportsLab/1.0 (historical research import)"}), timeout=35) as response:
        return response.read().decode("utf-8-sig")

def date_valid(value):
    try:
        parsed = dt.date.fromisoformat(value)
        return parsed <= dt.date.today()
    except (TypeError, ValueError):
        return False

def historical_fights(rows):
    accepted, rejected, seen = [], [], set()
    for index, row in enumerate(rows, 2):
        key = (row.get("fight_url") or "").strip()
        a, b = (row.get("f1_name") or "").strip(), (row.get("f2_name") or "").strip()
        ra, rb = row.get("f1_result"), row.get("f2_result")
        if not key.startswith(("http://ufcstats.com/fight-details/", "http://www.ufcstats.com/fight-details/")) or key in seen or not a or not b or a == b or not date_valid(row.get("date")) or (ra, rb) not in (("W","L"),("L","W")):
            rejected.append(index)
            continue
        seen.add(key)
        accepted.append({"source_fight_url":key,"event_date":row["date"],"event":row.get("event_name"),
                         "winner":a if ra=="W" else b,"loser":b if ra=="W" else a,
                         "method":row.get("method") or None,"scheduled_format":row.get("time_format"),
                         "result_source":"TidyTuesday 2026-07-07 snapshot","independently_verified":False})
    return accepted, rejected

def modeling_rows(rows):
    accepted, rejected, seen = [], [], set()
    for index, row in enumerate(rows, 2):
        a,b=(row.get("r_fighter") or "").strip(),(row.get("b_fighter") or "").strip()
        date=row.get("date")
        key=(date,a,b)
        if not date_valid(date) or not a or not b or a==b or key in seen or row.get("winner") not in ("Red","Blue"):
            rejected.append(index)
            continue
        seen.add(key)
        # Explicit allowlist: no post-fight finish, result, score or time.
        features={}
        for field in FEATURES:
            value=row.get(field)
            if value not in (None,"","NA"):
                try: features[field]=float(value)
                except ValueError: pass
        accepted.append({"date":date,"red":a,"blue":b,"features":features,
                         "outcome":{"winner":row["winner"]},
                         "historical_odds_unverified":{"red":row.get("r_odds"),"blue":row.get("b_odds")},
                         "source":"TidyTuesday 2026-07-07 snapshot",
                         "pre_fight_feature_timing_verified":False,
                         "odds_timestamp_verified":False,"bet_eligible":False})
    return accepted,rejected

def import_data(source_dir=None):
    fights, f_bad = historical_fights(rows_from_text(get_source(FILES[0],source_dir)))
    models, m_bad = modeling_rows(rows_from_text(get_source(FILES[1],source_dir)))
    return {"schema":1,"sport":"UFC","snapshot":"2026-07-07","research_only":True,"bet_eligible":False,
            "provenance":{"source":"rfordatascience/tidytuesday","url":BASE,
                          "upstream_sources":"fightr compilation; see original README",
                          "license_and_redistribution_review":"PENDING",
                          "independent_result_verification":False},
            "fight_history":{"rows":fights,"rejected_count":len(f_bad)},
            "modeling":{"rows":models,"rejected_count":len(m_bad)},
            "blockers":["LICENSE_REVIEW","INDEPENDENT_SOURCE_VERIFICATION",
                        "PREFIGHT_FEATURE_TIMING_UNVERIFIED","HISTORICAL_ODDS_TIMESTAMP_UNVERIFIED",
                        "OUT_OF_SAMPLE_CALIBRATION"]}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-dir",help="Directory containing previously downloaded source CSVs")
    parser.add_argument("--output",default="feed/ufc_tidytuesday_research.json")
    args=parser.parse_args()
    result=import_data(args.source_dir)
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("UFC imported historical fights:",len(result["fight_history"]["rows"]),
          "modeling rows:",len(result["modeling"]["rows"]),
          "bet_eligible:",result["bet_eligible"])

if __name__=="__main__":
    main()
