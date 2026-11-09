#!/usr/bin/env python3
"""Capped NFL event-level player-prop snapshot; scheduled and manual runs.
MAX_EVENTS caps per-event requests; API credits vary by market and bookmaker.
"""
import json, os, sys, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

SPORT="americanfootball_nfl"
MARKETS=("player_pass_yds","player_pass_tds","player_rush_yds",
         "player_reception_yds","player_receptions","player_anytime_td")
BOOKS=("fanduel","draftkings")
BASE="https://api.the-odds-api.com/v4/sports/"+SPORT

def request_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"KennysSportsLab/1.0"})
    with urllib.request.urlopen(req,timeout=40) as response:
        return json.load(response),response.headers.get("x-requests-remaining")

def extract(event, data):
    rows=[]
    for book in data.get("bookmakers",[]):
        if book.get("key") not in BOOKS:continue
        for market in book.get("markets",[]):
            if market.get("key") not in MARKETS:continue
            for outcome in market.get("outcomes",[]):
                price=outcome.get("price")
                if not isinstance(price,(int,float)) or -100<price<100:continue
                rows.append({
                    "event_id":event["id"],"event":event["away_team"]+" @ "+event["home_team"],
                    "commence_time":event.get("commence_time"),"market":market["key"],
                    "player":outcome.get("description"),"selection":outcome.get("name"),
                    "point":outcome.get("point"),"price":price,"bookmaker":book["key"],
                    "updated_at":market.get("last_update") or book.get("last_update")
                })
    return rows

def eligible_events(events, now):
    """Only valid future kickoffs; fail closed on malformed or naive timestamps."""
    upcoming=[]
    for e in events:
        if not all(e.get(k) for k in ("id","commence_time","away_team","home_team")):continue
        try:
            kickoff=datetime.fromisoformat(e["commence_time"].replace("Z","+00:00"))
            if kickoff.tzinfo is not None and kickoff>now:upcoming.append(e)
        except (ValueError,TypeError,AttributeError):pass
    return sorted(upcoming,key=lambda e:e["commence_time"])

def free_plan_budget_guard(now, prior_path=Path("feed/nfl_props.json"), reserve=20):
    """Avoid paid-credit calls when same-month published remaining balance is low."""
    if not prior_path.exists():return None
    try:
        previous=json.loads(prior_path.read_text())
        remaining=int(previous.get("remaining_credits"))
        fetched=datetime.fromisoformat(previous["fetched_at"].replace("Z","+00:00"))
        if fetched.tzinfo is None or fetched.astimezone(timezone.utc).strftime("%Y-%m")!=now.astimezone(timezone.utc).strftime("%Y-%m"):return None
        if remaining<=reserve:return remaining
    except (ValueError,TypeError,KeyError,OSError,AttributeError):
        pass
    return None

def reusable_event_ids(events, prior, now, max_age_minutes=30):
    """Skip a paid request only if both books and every required market are fresh."""
    valid={e["id"] for e in events}
    by_event={}
    for row in prior.get("odds",[]):
        eid=row.get("event_id")
        if eid not in valid or row.get("bookmaker") not in BOOKS or row.get("market") not in MARKETS:continue
        try:
            updated=datetime.fromisoformat(row["updated_at"].replace("Z","+00:00"))
            if updated.tzinfo is None or not 0<=(now-updated).total_seconds()<=max_age_minutes*60:continue
        except (ValueError,TypeError,KeyError,AttributeError):continue
        by_event.setdefault(eid,set()).add((row["bookmaker"],row["market"]))
    expected={(book,market) for book in BOOKS for market in MARKETS}
    return {eid for eid,pairs in by_event.items() if expected.issubset(pairs)}

def main():
    key=os.environ.get("THE_ODDS_API_KEY")
    if not key:print("Missing secret");return 2
    try:limit=int(os.environ.get("MAX_EVENTS","0"))
    except ValueError:return 2
    if not 1<=limit<=20:
        print("Choose MAX_EVENTS between 1 and 20 explicitly; no requests made");return 2
    # Never use a published snapshot's old balance as the current key's quota.
    # The events endpoint is free and returns live x-requests-remaining.
    query=lambda d:urllib.parse.urlencode(d)
    common={"apiKey":key,"bookmakers":",".join(BOOKS),"oddsFormat":"american"}
    try:
        events,remaining=request_json(BASE+"/events?"+query({"apiKey":key}))
        if not isinstance(events,list):raise ValueError("Unexpected events response")
        if remaining is None or not str(remaining).isdigit():
            print("FREE_PLAN_BUDGET_GUARD: live provider balance unavailable; no paid event requests")
            return 2
        print("LIVE_PROVIDER_CREDITS_REMAINING",remaining)
        if int(remaining)<=20:
            print("FREE_PLAN_BUDGET_GUARD: live balance",remaining,"<= reserve 20; no paid event requests")
            return 0
        now=datetime.now(timezone.utc)
        upcoming=eligible_events(events,now)
        print("Provider events",len(events),"eligible future events",len(upcoming))
        events=upcoming
        schedule_games=[{"event_id":e["id"],"event":e["away_team"]+" @ "+e["home_team"],"commence_time":e["commence_time"]} for e in upcoming]
        target_date=os.environ.get("TARGET_DATE")
        if target_date:
            datetime.strptime(target_date,"%Y-%m-%d")
            events=[e for e in events if datetime.fromisoformat(e["commence_time"].replace("Z","+00:00")).astimezone(ZoneInfo("America/New_York")).date().isoformat()==target_date]
            print("Target date",target_date,"games",len(events))
        expected=len(events)
        retry_missing=os.environ.get("RETRY_MISSING_ONLY","0")=="1"
        prior_coverage={}
        coverage_path=Path("feed/nfl_prop_capture_coverage.json")
        if retry_missing and coverage_path.exists():
            prior_coverage=json.loads(coverage_path.read_text())
            missing=set(prior_coverage.get("missing_event_ids",[]))
            events=[e for e in events if e["id"] in missing or e["id"] not in set(prior_coverage.get("captured_event_ids",[]))]
            print("Retry missing events",len(events))
        prior_path=Path("feed/nfl_props.json")
        prior=json.loads(prior_path.read_text()) if prior_path.exists() else {}
        current_ids={e["id"] for e in upcoming}
        cached=reusable_event_ids(events,prior,now)
        events=[e for e in events if e["id"] not in cached][:limit]
        print("Fresh complete-event cache hits",len(cached),"paid requests avoided")
        if not events:
            print("No new event requests needed; existing published feed retained")
            return 0
        rows=[];errors=[];captured=[];attempted=[]
        for event in events:
            if remaining is not None and str(remaining).isdigit() and int(remaining)<=20:
                print("FREE_PLAN_BUDGET_GUARD: stopping event requests at",remaining,"credits")
                break
            attempted.append(event["id"])
            try:
                payload,remaining=request_json(BASE+"/events/"+urllib.parse.quote(event["id"],safe="")+"/odds?"+query({**common,"markets":",".join(MARKETS)}))
                selections=extract(event,payload)
                rows.extend(selections)
                if selections:captured.append(event["id"])
                else:errors.append({"event_id":event["id"],"error":"no_supported_bookmaker_props"})
                print(event["id"],"selections",len(rows),"credits remaining",remaining)
            except (urllib.error.HTTPError,urllib.error.URLError,ValueError) as exc:
                errors.append({"event_id":event["id"],"error":type(exc).__name__})
                print("Event unavailable",event["id"],type(exc).__name__)
        # Preserve every unattempted upcoming event's quote history. Old timestamps
        # remain unchanged so the UI cannot mistake cached prices for fresh odds.
        old_rows=[o for o in prior.get("odds",[]) if o.get("event_id") in current_ids and o.get("event_id") not in set(attempted)]
        rows=old_rows+rows
        print("Preserved unattempted upcoming event selections",len(old_rows))
        unique={}
        for o in rows:
            k=(o.get("event_id"),o.get("bookmaker"),o.get("market"),o.get("player"),o.get("selection"),o.get("point"))
            unique[k]=o
        rows=list(unique.values())
        available_ids={o.get("event_id") for o in rows}
        captured=[e["id"] for e in upcoming if e["id"] in available_ids]
        missing_ids=[e["id"] for e in upcoming if e["id"] not in available_ids]
        coverage={"schedule_games":schedule_games,"generated_at":datetime.now(timezone.utc).isoformat(),"target_date":target_date or None,"expected_upcoming_events":expected,"requested_events":len(attempted),"cached_complete_events":len(cached),"captured_event_ids":captured,"captured_events":len(captured),"missing_event_ids":missing_ids,"unrequested_events":max(0,expected-len(events)) if not retry_missing else 0,"complete":not missing_ids and not errors,"requested_scope_complete":bool(attempted) and all(eid in available_ids for eid in attempted) and not errors,"errors":errors,"status":"COMPLETE" if not missing_ids and not errors else "PARTIAL","requested_scope_status":"COMPLETE" if attempted and all(eid in available_ids for eid in attempted) and not errors else "PARTIAL","retry_missing_only":retry_missing,"attempted_event_ids":attempted}
        Path("feed/nfl_prop_capture_coverage.json").write_text(json.dumps(coverage,indent=2)+chr(10))
        print("CAPTURE_COVERAGE",json.dumps(coverage))
        if not rows:print("No verified prop prices returned; old feed preserved");return 1
        output={"source":"the-odds-api-v4-event-props","sport":SPORT,
                "fetched_at":datetime.now(timezone.utc).isoformat(),
                "markets_requested":list(MARKETS),"books":list(BOOKS),
                "events_requested":len(events),"errors":errors,
                "remaining_credits":remaining,"schedule_games":schedule_games,"odds":rows}
        path=Path("feed/nfl_props.json");path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(output,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
        print("Saved",len(rows),"verified prop prices")
        return 0
    except (urllib.error.HTTPError,urllib.error.URLError,ValueError) as exc:
        print("Provider unavailable",type(exc).__name__);return 1
if __name__=="__main__":sys.exit(main())
