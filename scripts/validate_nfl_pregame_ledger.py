#!/usr/bin/env python3
"""Fail-closed validator for append-only NFL pregame prop snapshots. No betting activation."""
import json, math, sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED=("snapshot_id","game_id","player_id","market","side","line","decimal_odds","probability","captured_at","kickoff_at","source","model_version")
MARKETS={"player_rush_yds","player_pass_yds","player_reception_yds","player_receptions"}

def timestamp(value):
    if not isinstance(value,str) or not value.endswith("Z"):
        raise ValueError("timestamps must be explicit UTC Z")
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None: raise ValueError("timezone missing")
    return dt.astimezone(timezone.utc)

def validate(rows):
    if not isinstance(rows,list): raise ValueError("expected snapshot list")
    seen=set()
    accepted=[]
    errors=[]
    for index,row in enumerate(rows):
        try:
            if not isinstance(row,dict): raise ValueError("snapshot must be object")
            missing=[key for key in REQUIRED if key not in row]
            if missing: raise ValueError("missing fields: "+",".join(missing))
            for key in ("snapshot_id","game_id","player_id","source","model_version"):
                if not isinstance(row[key],str) or not row[key].strip(): raise ValueError("invalid "+key)
            if row["snapshot_id"] in seen: raise ValueError("duplicate snapshot_id")
            seen.add(row["snapshot_id"])
            if row["market"] not in MARKETS: raise ValueError("unsupported market")
            if row["side"] not in ("over","under"): raise ValueError("invalid side")
            for key in ("line","decimal_odds","probability"):
                if isinstance(row[key],bool) or not isinstance(row[key],(int,float)) or not math.isfinite(row[key]):
                    raise ValueError("invalid "+key)
            if row["line"]<0 or row["decimal_odds"]<=1 or not 0<row["probability"]<1:
                raise ValueError("out-of-range numerical input")
            if timestamp(row["captured_at"])>=timestamp(row["kickoff_at"]):
                raise ValueError("snapshot not before kickoff")
            accepted.append(row["snapshot_id"])
        except (ValueError,TypeError,OverflowError) as exc:
            errors.append({"index":index,"reason":str(exc)})
    return {"status":"VALID" if not errors and accepted else "BLOCKED",
            "validated_snapshots":len(accepted),"rejected_snapshots":len(errors),
            "errors":errors,"bet_eligibility":"BLOCKED",
            "warning":"This validates snapshot structure and timing, not authenticity, independent capture, forecast accuracy or profitability."}

if __name__=="__main__":
    rows=json.loads(Path(sys.argv[1]).read_text())
    result=validate(rows)
    print(json.dumps(result,indent=2))
    if result["status"]!="VALID": sys.exit(1)
