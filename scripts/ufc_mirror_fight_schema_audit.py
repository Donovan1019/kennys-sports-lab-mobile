#!/usr/bin/env python3
"""Inspect UFCStats public mirror fight rows before historical feature conversion.

Fail closed: do not invent fight dates, round exposure, or settlement status.
"""
import argparse,csv,io,json
from pathlib import Path
from urllib.request import Request,urlopen
from scripts.ufc_public_mirror_ingest import BASE

def inspect(rows):
    if not rows:raise ValueError("empty fight statistics mirror")
    cols=set(rows[0])
    required={"FIGHTER","SIG.STR.","TD","CTRL"}
    if not required.issubset(cols):raise ValueError("missing columns: "+str(sorted(required-cols)))
    candidates={
        "fight_id":[c for c in cols if any(t in c.upper() for t in ("FIGHT_ID","BOUT_ID","FIGHT URL","FIGHT_URL"))],
        "fight_time":[c for c in cols if any(t in c.upper() for t in ("DATE","EVENT_TIME","FIGHT_TIME"))],
        "round":[c for c in cols if c.upper() in ("ROUND","RND")],
        "round_duration":[c for c in cols if any(t in c.upper() for t in ("DURATION","ROUND_TIME","ELAPSED"))],
        "result":[c for c in cols if c.upper() in ("RESULT","WINNER","OUTCOME","W/L")],
    }
    missing=[k for k,v in candidates.items() if not v]
    return {"rows":len(rows),"columns":sorted(cols),"candidate_columns":candidates,
            "missing_historical_fields":missing,
            "can_generate_point_in_time_training_rows":not missing,
            "warning":"Column presence alone is not sufficient; validate event chronology, row grain, settlement and original publication."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",default=BASE+"ufc_fight_stats.csv")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.source.startswith("https://"):
        if args.source!=BASE+"ufc_fight_stats.csv":raise ValueError("unapproved remote source")
        with urlopen(Request(args.source,headers={"User-Agent":"KennysSportsLabResearch/1.0"}),timeout=35) as response:
            raw=response.read(18_000_000).decode("utf-8-sig")
    else:raw=Path(args.source).read_text(encoding="utf-8-sig")
    result=inspect(list(csv.DictReader(io.StringIO(raw))))
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
