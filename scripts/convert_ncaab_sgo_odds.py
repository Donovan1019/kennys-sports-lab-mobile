#!/usr/bin/env python3
"""Convert existing verified SportsGameOdds DK/FD feed to NCAAB page contract."""
import datetime as dt
import json
from pathlib import Path

SOURCE=Path("feed/basketball_ncaab.json")
DEST=Path("data/ncaab_odds.json")
def convert(payload, now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    if payload.get("source")!="sportsgameodds-v2" or payload.get("sport")!="basketball_ncaab" or payload.get("status")!="ok":
        raise ValueError("Unexpected provider feed")
    fetched=dt.datetime.fromisoformat(payload["fetched_at"].replace("Z","+00:00"))
    if not dt.timedelta(0)<=now-fetched<=dt.timedelta(hours=6):
        raise ValueError("Stale source feed")
    events={}
    for row in payload.get("odds",[]):
        if row.get("sport")!="basketball_ncaab" or row.get("market") not in ("h2h","spreads","totals"):
            continue
        book=row.get("bookmaker")
        if book not in ("draftkings","fanduel"):
            continue
        try:
            start=dt.datetime.fromisoformat(row["commence_time"].replace("Z","+00:00"))
            updated=dt.datetime.fromisoformat(row["updated_at"].replace("Z","+00:00"))
            price=int(row["price"])
        except (KeyError,ValueError,TypeError):
            continue
        if not (start>now and dt.timedelta(0)<=now-updated<=dt.timedelta(hours=6) and (price>=100 or price<=-100)):
            continue
        eventname=row.get("event","")
        if " @ " not in eventname: continue
        away,home=eventname.split(" @ ",1)
        if not away or not home or row.get("selection") not in (home,away,"Over","Under"):continue
        market=row["market"]
        if market=="h2h" and row["selection"] not in (home,away):continue
        if market=="totals" and row["selection"] not in ("Over","Under"):continue
        if market=="spreads" and row["selection"] not in (home,away):continue
        outcome={"name":row["selection"],"price":price}
        if market!="h2h":
            try:outcome["point"]=float(row["point"])
            except (TypeError,ValueError):continue
        key=(row["event_id"],row["commence_time"],home,away)
        event=events.setdefault(key,{"id":str(row["event_id"]),"commence_time":row["commence_time"],"home_team":home,"away_team":away,"bookmakers":{}})
        b=event["bookmakers"].setdefault(book,{"key":book,"title":{"draftkings":"DraftKings","fanduel":"FanDuel"}[book],"last_update":row["updated_at"],"markets":{}})
        m=b["markets"].setdefault(market,{"key":market,"outcomes":[]})
        if not any(o["name"]==outcome["name"] and o.get("point")==outcome.get("point") for o in m["outcomes"]):
            m["outcomes"].append(outcome)
    result=[]
    for event in events.values():
        books=[]
        for b in event["bookmakers"].values():
            markets=[]
            for m in b["markets"].values():
                names={o["name"] for o in m["outcomes"]}
                expected={event["home_team"],event["away_team"]} if m["key"]!="totals" else {"Over","Under"}
                if names==expected and len(m["outcomes"])==2:markets.append(m)
            if markets:
                b["markets"]=markets
                books.append(b)
        if books:
            event["bookmakers"]=books
            result.append(event)
    if not result:raise ValueError("No complete fresh NCAA sportsbook markets")
    return {"sport":"basketball_ncaab","source":"sportsgameodds-v2","fetched_at":now.isoformat(),"events":result}
def main():
    payload=json.loads(SOURCE.read_text())
    result=convert(payload)
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(result,separators=(",",":"))+"\n")
    print("NCAAB SportsGameOdds validated events:",len(result["events"]))
if __name__=="__main__":main()
