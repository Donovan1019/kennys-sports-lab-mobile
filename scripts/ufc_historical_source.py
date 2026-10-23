#!/usr/bin/env python3
"""Historical ESPN UFC scoreboard collector; explicit dates, strict result verification.
No claim of complete historical coverage. Review licensing and source before production.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE="https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"

def fetch_day(day):
    url=BASE+"?"+urlencode({"dates":day.strftime("%Y%m%d")})
    with urlopen(Request(url,headers={"User-Agent":"KennysSportsLab/1.0 (historical research)"}),timeout=20) as response:
        return json.load(response)

def athlete_name(row):
    a=row.get("athlete") or {}
    return a.get("displayName") or row.get("displayName") or ""

def parse_day(payload,day):
    rows=[]
    seen=set()
    for event in payload.get("events",[]):
        for bout in event.get("competitions",[]):
            if (bout.get("status") or {}).get("type",{}).get("completed") is not True:
                continue
            contestants=bout.get("competitors") or []
            if len(contestants)!=2:
                continue
            winners=[c for c in contestants if c.get("winner") is True]
            losers=[c for c in contestants if c.get("winner") is False]
            if len(winners)!=1 or len(losers)!=1:
                continue
            winner=athlete_name(winners[0]).strip()
            loser=athlete_name(losers[0]).strip()
            fid=str(bout.get("id") or "").strip()
            eid=str(event.get("id") or "").strip()
            date=bout.get("date") or event.get("date")
            if not all((winner,loser,fid,eid,date)) or winner==loser:
                continue
            try:
                when=dt.datetime.fromisoformat(date.replace("Z","+00:00"))
                if when.tzinfo is None or when.date()>day:
                    continue
            except (ValueError,AttributeError):
                continue
            # ESPN status fields are not consistently mapped to official methods.
            # Only accept an explicit normalized method from verified details.
            method=bout.get("verified_method")
            if method not in ("KO/TKO","Submission","Decision"):
                continue
            key=(eid,fid)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"event_id":eid,"fight_id":fid,"event_date":when.isoformat(),
                         "winner":winner,"loser":loser,"method":method,
                         "source_url":BASE+"?"+urlencode({"dates":day.strftime("%Y%m%d")})})
    return rows

def collect(start,end,max_days=31):
    if end<start or (end-start).days+1>max_days:
        raise ValueError("Invalid date range or exceeds 31-day request limit")
    rows=[]
    errors=[]
    day=start
    while day<=end:
        try:
            payload=fetch_day(day)
            rows.extend(parse_day(payload,day))
        except (OSError,ValueError,KeyError) as exc:
            errors.append({"day":day.isoformat(),"error":str(exc)})
        day+=dt.timedelta(days=1)
    return {"results":rows,"source":"ESPN public MMA scoreboard; strict method verification",
            "coverage_days":(end-start).days+1,"failed_days":errors,
            "excluded_unverified_methods":True,"bet_eligible":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--start",required=True)
    p.add_argument("--end",required=True)
    p.add_argument("--output",default="feed/ufc_historical_source.json")
    args=p.parse_args()
    start=dt.date.fromisoformat(args.start)
    end=dt.date.fromisoformat(args.end)
    if end>=dt.datetime.now(dt.timezone.utc).date():
        raise SystemExit("Only completed prior UTC dates accepted")
    report=collect(start,end)
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(f"Verified rows={len(report['results'])}; failed days={len(report['failed_days'])}; method-unverified fights excluded")
if __name__=="__main__":
    main()
