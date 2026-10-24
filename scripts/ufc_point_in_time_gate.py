#!/usr/bin/env python3
"""UFC point-in-time feature eligibility gate.

A retrospective data mirror is NEVER proof a statistic existed before a bout.
Only source snapshots captured before the prediction cutoff are permitted.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

def parse_time(value):
    if not isinstance(value,str) or not value.strip():
        raise ValueError("missing timestamp")
    parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("naive timestamp")
    return parsed.astimezone(timezone.utc)

def validate(record):
    required=("fight_id","fighter_id","feature_name","value","source_event_time",
              "source_published_at","captured_at","prediction_cutoff","source_sha256")
    missing=[k for k in required if k not in record or record[k] in (None,"")]
    if missing:raise ValueError("missing fields: "+",".join(missing))
    if not str(record["fight_id"]).strip() or not str(record["fighter_id"]).strip():
        raise ValueError("blank fight/fighter id")
    published=parse_time(record["source_published_at"])
    captured=parse_time(record["captured_at"])
    event=parse_time(record["source_event_time"])
    cutoff=parse_time(record["prediction_cutoff"])
    if event>published:raise ValueError("source event after publication")
    if published>captured:raise ValueError("publication after capture")
    if captured>cutoff:raise ValueError("feature snapshot captured after prediction cutoff")
    if event>=cutoff:raise ValueError("feature event not prior to prediction")
    digest=str(record["source_sha256"]).lower()
    if len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("invalid source SHA256")
    return True

def audit(records):
    accepted=[]
    rejected=[]
    keys=set()
    for index,row in enumerate(records):
        try:
            validate(row)
            key=(row["fight_id"],row["fighter_id"],row["feature_name"],row["prediction_cutoff"])
            if key in keys:raise ValueError("duplicate feature key")
            keys.add(key)
            accepted.append(row)
        except (ValueError,TypeError,KeyError) as exc:
            rejected.append({"index":index,"reason":str(exc)})
    return {"accepted":len(accepted),"rejected":len(rejected),"rejections":rejected}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("json_path",type=Path)
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    rows=json.loads(args.json_path.read_text())
    if not isinstance(rows,list):raise SystemExit("Expected JSON list of feature records")
    result=audit(rows)
    report=json.dumps(result,indent=2)
    if args.report:args.report.write_text(report+"\n")
    print(report)
    if result["rejected"] or not result["accepted"]:raise SystemExit(1)

if __name__=="__main__":main()
