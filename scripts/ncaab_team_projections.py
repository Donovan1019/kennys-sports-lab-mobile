#!/usr/bin/env python3
"""Build point-in-time NCAA team score projections from completed ESPN boxscores.

Research projections only: no odds, probability, EV, injury, or roster adjustment.
"""
import collections
import datetime as dt
import json
import pathlib
import statistics
from ncaab_research_backtest import eligible_game, season_key, team_key

SOURCE=pathlib.Path("data/ncaab_espn_history.json")
OUTPUT=pathlib.Path("data/ncaab_team_projections.json")
MIN_GAMES=5

def build(games):
    valid=sorted((g for g in games if eligible_game(g)),key=lambda g:(g["date"],g["event_id"]))
    if not valid:return {}
    latest=season_key(dt.datetime.now(dt.timezone.utc).date().isoformat())
    history=collections.defaultdict(list)
    for g in valid:
        if season_key(g["date"])!=latest:continue
        a,b=g["teams"]
        pace=(a["possessions_est"]+b["possessions_est"])/2
        for t,opp in ((a,b),(b,a)):
            history[team_key(t)].append({"name":t["name"],"pace":pace,
              "off":100*t["points"]/t["possessions_est"],
              "def":100*opp["points"]/opp["possessions_est"],
              "date":g["date"]})
    result={}
    progress={}
    provisional={}
    counts=collections.Counter()
    for k,rows in history.items():
        progress[k]={"team":rows[-1]["name"],"games":len(rows),"needed":max(0,MIN_GAMES-len(rows))}
        counts["observed"]+=1
        if len(rows)<MIN_GAMES:
            counts["insufficient_current_season_games"]+=1
            # Diagnostic only: do not silently promote sparse teams to betting eligibility.
            window=rows[-15:]
            provisional[k]={"team":rows[-1]["name"],"games":len(rows),
                            "pace":round(statistics.mean(x["pace"] for x in window),3),
                            "off":round(statistics.mean(x["off"] for x in window),3),
                            "def":round(statistics.mean(x["def"] for x in window),3),
                            "status":"PROVISIONAL_NOT_CALIBRATED"}
            continue
        counts["eligible"]+=1
        window=rows[-15:]
        result[k]={"team_id":k,"team":rows[-1]["name"],"games":len(rows),
          "pace":round(statistics.mean(x["pace"] for x in window),3),
          "off":round(statistics.mean(x["off"] for x in window),3),
          "def":round(statistics.mean(x["def"] for x in window),3),
          "last_game":rows[-1]["date"]}
    return {"season":latest,"teams":result,"minimum_games":MIN_GAMES,
            "observed_teams":len(progress),"eligible_teams":len(result),
            "team_progress":progress,"provisional_teams":provisional,
            "ineligible_reasons":dict(counts),
            "coverage_policy":"Five completed current-season games per team; provisional estimates are research only"}

def main():
    src=json.loads(SOURCE.read_text())
    result=build(src.get("games",[]))
    payload={"provider":"espn-public","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
      "source_fetched_at":src.get("fetched_at"),"research_only":True,
      "model":"unadjusted-last-15-pace-efficiency","coverage":result,
      "limitations":["No opponent adjustment or injury model","No calibrated probabilities, fair odds or EV"]}
    OUTPUT.write_text(json.dumps(payload,separators=(",",":"))+"\n")
    print("NCAA research projection teams:",len(result.get("teams",{})))
if __name__=="__main__":main()
