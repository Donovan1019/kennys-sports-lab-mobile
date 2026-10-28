"""Archive only timestamp-verified NBA quotes; never synthesize SGP picks."""
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FEED=ROOT/"feed"
def stamp(s):
    try:
        d=datetime.fromisoformat(str(s).replace("Z","+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (TypeError,ValueError,AttributeError):
        return None

def capture(now=None):
    now=now or datetime.now(timezone.utc)
    source=FEED/"nba_props.json"
    try: data=json.loads(source.read_text())
    except (OSError,ValueError): data={}
    fetched=stamp(data.get("fetched_at"))
    fresh=bool(fetched and 0<=(now-fetched).total_seconds()<=86400)
    rows=data.get("odds",[])
    if not isinstance(rows,list): rows=[]
    ledger=FEED/"nba_prop_pregame_ledger.jsonl"
    existing=[]
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            try: existing.append(json.loads(line))
            except ValueError: continue
    keys=("event_id","market","player","selection","point","bookmaker","updated_at")
    identity=lambda row:tuple(str(row.get(k)) for k in keys)
    seen={identity(row) for row in existing}
    new=[];rejected={}
    for row in rows:
        reason=None
        if not isinstance(row,dict): reason="invalid_row"
        else:
            tip=stamp(row.get("commence_time"))
            updated=stamp(row.get("updated_at"))
            if not fresh: reason="stale_feed"
            elif not tip or not updated or not (updated<=fetched<=now<tip): reason="invalid_pregame_timestamp"
            elif (now-updated).total_seconds()>86400: reason="stale_quote"
            elif not all(row.get(k) for k in ("event_id","event","market","player","bookmaker")): reason="missing_identity"
            elif row.get("market") not in ("player_points","player_rebounds","player_assists","player_threes"): reason="unsupported_market"
            elif row.get("selection") not in ("Over","Under"): reason="invalid_side"
            elif not isinstance(row.get("point"),(int,float)) or isinstance(row.get("point"),bool): reason="invalid_line"
            elif not isinstance(row.get("price"),(int,float)) or isinstance(row.get("price"),bool): reason="invalid_price"
        if reason: rejected[reason]=rejected.get(reason,0)+1
        elif identity(row) not in seen:
            seen.add(identity(row))
            new.append(dict(row,captured_at=now.isoformat(),snapshot_source="automated-existing-odds-feed",settlement_status="NOT_PLACED"))
    if new:
        with ledger.open("a") as out:
            for row in new: out.write(json.dumps(row,separators=(",",":"))+"\n")
    sgp=FEED/"nba_sgp_pregame_ledger.jsonl"
    sgp_count=sum(bool(line.strip()) for line in sgp.read_text().splitlines()) if sgp.exists() else 0
    report={"generated_at":now.isoformat(),"feed_fresh":fresh,"new_verified_pregame_quotes":len(new),
            "total_quote_records":len(existing)+len(new),"saved_explicit_sgp_records":sgp_count,
            "rejected":rejected,"sgp_status":"AVAILABLE_FOR_GRADING" if sgp_count else "NO_ACTUAL_SGP_RECOMMENDATIONS",
            "betting_ready":False,"note":"No illustrated picks, synthetic combinations, or assumed bets. Live odds refresh is not provided by this capture."}
    (FEED/"nba_automation_coverage.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
    return report

if __name__=="__main__": capture()
