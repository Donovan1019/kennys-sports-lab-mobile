"""Validate and append a copied NBA SGP JSON snapshot without inventing a bet."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone

LEDGER=Path("feed/nba_sgp_pregame_ledger.jsonl")
def stamp(value):
    try:
        d=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError,TypeError,AttributeError):
        return None

def ingest(record):
    if not isinstance(record,dict) or record.get("schema_version")!=1:
        raise ValueError("Unsupported snapshot schema")
    event=str(record.get("event_id") or "")
    sid=str(record.get("sgp_id") or "")
    captured=stamp(record.get("captured_at"))
    tip=stamp(record.get("commence_time"))
    legs=record.get("legs")
    if not event or not sid or not captured or not tip or captured>=tip:
        raise ValueError("Missing identity or invalid pregame capture time")
    if not isinstance(legs,list) or not 2<=len(legs)<=6:
        raise ValueError("Expected 2–6 selected legs")
    if record.get("settlement_status")!="NOT_PLACED":
        raise ValueError("Snapshot is not proof of a placed wager")
    for leg in legs:
        if not isinstance(leg,dict) or str(leg.get("event_id"))!=event:
            raise ValueError("Mixed or missing game event")
        if stamp(leg.get("captured_at"))!=captured or stamp(leg.get("commence_time"))!=tip:
            raise ValueError("Inconsistent leg capture/tipoff")
        quote=stamp(leg.get("updated_at"))
        if not quote or quote>captured or quote>=tip:
            raise ValueError("Invalid quote timestamp")
        if leg.get("market") not in ("player_points","player_rebounds","player_assists","player_threes"):
            raise ValueError("Unsupported player prop market")
        if leg.get("selection") not in ("Over","Under") or not leg.get("player") or not leg.get("bookmaker"):
            raise ValueError("Missing side/player/book")
        try:
            line=float(leg["point"])
            if not 0<=line<1000: raise ValueError("Invalid threshold")
        except (KeyError,TypeError,ValueError):
            raise ValueError("Invalid threshold")
    existing=[]
    if LEDGER.exists():
        existing=[json.loads(x) for x in LEDGER.read_text().splitlines() if x.strip()]
    if any(x.get("sgp_id")==sid for x in existing):
        raise ValueError("Duplicate snapshot ID")
    LEDGER.parent.mkdir(parents=True,exist_ok=True)
    with LEDGER.open("a") as out:
        out.write(json.dumps(record,separators=(",",":"))+"\n")
    print("Saved research-only snapshot",sid,"(NOT a verified placed bet)")

if __name__=="__main__":
    ingest(json.loads(Path(sys.argv[1]).read_text()))
