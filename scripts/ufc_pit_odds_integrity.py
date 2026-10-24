"""Point-in-time UFC two-sided odds integrity audit.

Do not silently treat a feed's fetched_at as the bookmaker's quote time.
A snapshot is actionable only if both quotes predate fight start, have
credible timestamps, identical bookmaker/event/market, and are fresh.
"""
from datetime import datetime,timezone
from collections import defaultdict
import json,argparse
from pathlib import Path

def parse_time(value):
    if not isinstance(value,str) or not value.strip():return None
    try:
        dt=datetime.fromisoformat(value.strip().replace("Z","+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except ValueError:return None

def implied(american):
    if isinstance(american,bool):return None
    try:
        price=float(american)
    except (TypeError,ValueError):return None
    if price==0 or not -100000<=price<=100000:return None
    return 100/(price+100) if price>0 else -price/(-price+100)

def audit(feed,now,max_age_hours=6):
    if not isinstance(now,datetime) or now.tzinfo is None:raise ValueError("now must be timezone-aware")
    now=now.astimezone(timezone.utc)
    fetched=parse_time(feed.get("fetched_at"))
    groups=defaultdict(list)
    for q in feed.get("odds",[]):
        if q.get("market")!="h2h":continue
        key=(q.get("event_id"),q.get("bookmaker"),q.get("market"))
        groups[key].append(q)
    results=[]
    for (event_id,book,market),quotes in sorted(groups.items(),key=lambda v:str(v[0])):
        problems=[]
        if len(quotes)!=2:problems.append("NOT_EXACTLY_TWO_SIDES")
        if len({q.get("selection") for q in quotes})!=2:problems.append("DUPLICATE_OR_MISSING_SELECTION")
        starts={q.get("commence_time") for q in quotes}
        if len(starts)!=1:problems.append("INCONSISTENT_START_TIME")
        start=parse_time(next(iter(starts))) if len(starts)==1 else None
        if start is None:problems.append("MISSING_START_TIME")
        if fetched is None:problems.append("MISSING_FETCH_TIMESTAMP")
        elif fetched>now:problems.append("FUTURE_FETCH_TIMESTAMP")
        probabilities=[]
        for q in quotes:
            t=parse_time(q.get("updated_at"))
            p=implied(q.get("price"))
            if t is None:problems.append("MISSING_BOOKMAKER_TIMESTAMP")
            else:
                if t>now:problems.append("FUTURE_QUOTE_TIMESTAMP")
                if (now-t).total_seconds()>max_age_hours*3600:problems.append("STALE_QUOTE")
                if fetched and t>fetched:problems.append("QUOTE_AFTER_FETCH")
                if start and t>=start:problems.append("QUOTE_AT_OR_AFTER_START")
            if p is None:problems.append("INVALID_PRICE")
            else:probabilities.append(p)
        if fetched and start and fetched>=start:problems.append("SNAPSHOT_AT_OR_AFTER_START")
        if start and now>=start:problems.append("FIGHT_STARTED")
        if len(probabilities)==2 and not .95<=sum(probabilities)<=1.5:
            problems.append("IMPLAUSIBLE_MARKET_OVERROUND")
        results.append({"event_id":event_id,"bookmaker":book,"market":market,
            "selections":[q.get("selection") for q in quotes],
            "status":"VERIFIED_PRE_FIGHT_QUOTE" if not problems else "RESEARCH_ONLY",
            "issues":sorted(set(problems)),
            "no_vig_probabilities":({quotes[i]["selection"]:probabilities[i]/sum(probabilities)
                for i in range(2)} if not problems else None)})
    return {"source":feed.get("source"),"snapshot_at":feed.get("fetched_at"),
        "evaluated_at":now.isoformat(),"max_age_hours":max_age_hours,
        "markets_checked":len(results),
        "verified_pre_fight_markets":sum(r["status"]=="VERIFIED_PRE_FIGHT_QUOTE" for r in results),
        "research_only_markets":sum(r["status"]!="VERIFIED_PRE_FIGHT_QUOTE" for r in results),
        "markets":results,
        "note":"Quote integrity does not establish fighter eligibility, opponent matchup accuracy, model calibration, or positive EV."}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--feed",type=Path,default=Path("feed/mma_mixed_martial_arts.json"))
    ap.add_argument("--output",type=Path,default=Path("ufc_pit_odds_audit.json"))
    ap.add_argument("--as-of",help="UTC ISO timestamp; default actual run time")
    args=ap.parse_args()
    now=parse_time(args.as_of) if args.as_of else datetime.now(timezone.utc)
    if now is None:raise SystemExit("invalid --as-of timestamp")
    result=audit(json.loads(args.feed.read_text()),now)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="markets"},indent=2))
if __name__=="__main__":main()
