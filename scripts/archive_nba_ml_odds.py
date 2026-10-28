#!/usr/bin/env python3
"""Point-in-time archive for future historical odds and CLV audits; never backfill fabricated quotes."""
import datetime as dt
import json
import pathlib

def snapshot(odds, model, now):
    try:
        fetched=dt.datetime.fromisoformat(odds["fetched_at"].replace("Z","+00:00"))
        generated=dt.datetime.fromisoformat(model["generated_at"].replace("Z","+00:00"))
        if odds.get("status")!="ok" or model.get("status")!="validated" or not (0 <= (now-fetched).total_seconds()<=150*60) or not (0 <= (now-generated).total_seconds()<=150*60):
            raise ValueError("Stale or invalid odds/model")
        ps={(str(x["event_id"]),str(x["team"])):x["win_probability"] for x in model["predictions"]}
        rows=[]
        for x in odds.get("odds",[]):
            try:
                tip=dt.datetime.fromisoformat(x["commence_time"].replace("Z","+00:00"))
                updated=dt.datetime.fromisoformat(x["updated_at"].replace("Z","+00:00"))
                key=(str(x["event_id"]),str(x["selection"]))
                price=int(x["price"])
                if x["market"]!="h2h" or key not in ps or tip<=now or updated>now or (now-updated).total_seconds()>150*60 or price==0:continue
                rows.append({"event_id":key[0],"event":x["event"],"commence_time":x["commence_time"],"bookmaker":x["bookmaker"],"selection":key[1],"price":price,"quote_updated_at":x["updated_at"],"model_probability":ps[key]})
            except (KeyError,ValueError,TypeError,OverflowError):continue
        return {"status":"ok","captured_at":now.isoformat(),"rows":rows,"historical_backtest_validated":False,"closing_line_verified":False}
    except (KeyError,ValueError,TypeError,AttributeError):
        return {"status":"unavailable","captured_at":now.isoformat(),"rows":[],"historical_backtest_validated":False,"closing_line_verified":False}

def main():
    now=dt.datetime.now(dt.timezone.utc)
    try:
        odds=json.loads(pathlib.Path("feed/basketball_nba.json").read_text())
        model=json.loads(pathlib.Path("feed/nba_ml_predictions.json").read_text())
        data=snapshot(odds,model,now)
    except (OSError,ValueError):
        data={"status":"unavailable","captured_at":now.isoformat(),"rows":[],"historical_backtest_validated":False,"closing_line_verified":False}
    day=now.strftime("%Y-%m-%d")
    stamp=now.strftime("%Y%m%dT%H%M%SZ")
    target=pathlib.Path("data/nba_ml_odds_archive")/day/(stamp+".json")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,separators=(",",":"))+"\n")
    print("NBA pregame odds archive:",data["status"],len(data["rows"]),target)
if __name__=="__main__":main()
