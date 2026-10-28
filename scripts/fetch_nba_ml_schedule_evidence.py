#!/usr/bin/env python3
"""Free ESPN NBA schedule/availability evidence. Never infer confirmed lineups."""
import datetime as dt
import json
import pathlib
import urllib.request
from zoneinfo import ZoneInfo

URL="https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={day}&limit=100"
def parse(data, now):
    events=[]
    for e in data.get("events",[]):
        try:
            comp=e["competitions"][0]
            sides={x["homeAway"]:x["team"]["displayName"] for x in comp["competitors"]}
            tip=dt.datetime.fromisoformat(e["date"].replace("Z","+00:00"))
            if tip.tzinfo is None:continue
            events.append({"event_id_espn":str(e["id"]),"home":sides["home"],"away":sides["away"],"commence_time":tip.isoformat(),"status":comp.get("status",{}).get("type",{}).get("name","unknown")})
        except (KeyError,IndexError,TypeError,ValueError):continue
    return {"status":"ok","source":"espn-public-scoreboard","fetched_at":now.isoformat(),"events":events,"confirmed_lineups":False,"injury_status_verified":False,"rest_verified":False}
def main():
    now=dt.datetime.now(dt.timezone.utc)
    day=now.astimezone(ZoneInfo("America/New_York")).strftime("%Y%m%d")
    req=urllib.request.Request(URL.format(day=day),headers={"User-Agent":"KennysSportsLab/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=20) as response: result=parse(json.load(response),now)
    except Exception as e:
        result={"status":"unavailable","source":"espn-public-scoreboard","fetched_at":now.isoformat(),"events":[],"confirmed_lineups":False,"injury_status_verified":False,"rest_verified":False,"reason":type(e).__name__}
    target=pathlib.Path("feed/nba_ml_schedule_evidence.json")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+"\n")
    print("NBA schedule evidence:",result["status"],len(result["events"]))
if __name__=="__main__":main()
