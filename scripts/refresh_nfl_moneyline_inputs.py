#!/usr/bin/env python3
"""Publish current NFL game schedule and completed scoring history from ESPN's public API.
No sportsbook odds, injuries, or starting lineup claims. Fail closed on source errors.
"""
import datetime as dt
import json
import os
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "feed" / "independent_game_inputs.json"
API = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
UTC = dt.timezone.utc

def fetch(day):
    url = API + "?dates=" + day.strftime("%Y%m%d") + "&limit=100"
    req = urllib.request.Request(url, headers={"User-Agent": "KSL-NFL-Research/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)

def parse(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))

def main():
    now = dt.datetime.now(UTC)
    # Week-level queries limit HTTP requests while covering recent history and next 3 weeks.
    days = sorted(set([now.date() + dt.timedelta(days=i) for i in range(-105, 0) if (now.date() + dt.timedelta(days=i)).weekday() in (0, 3, 6)] + [now.date() + dt.timedelta(days=i) for i in range(0, 22)]))
    events = {}
    successful = 0
    for day in days:
        try:
            data = fetch(day)
            successful += 1
            for event in data.get("events", []):
                events[str(event["id"])] = event
        except Exception as exc:
            print("ESPN fetch failed:", day, exc)
    if successful < len(days):
        raise RuntimeError("Incomplete ESPN source coverage; refusing to publish partial feed")
    history = {}
    upcoming = []
    for event in events.values():
        comps = event.get("competitions", [])
        if not comps:
            continue
        comp = comps[0]
        sides = comp.get("competitors", [])
        if len(sides) != 2:
            continue
        home = next((s for s in sides if s.get("homeAway") == "home"), None)
        away = next((s for s in sides if s.get("homeAway") == "away"), None)
        if not home or not away:
            continue
        home_name = home.get("team", {}).get("displayName")
        away_name = away.get("team", {}).get("displayName")
        if not home_name or not away_name:
            continue
        when = parse(event["date"])
        status = event.get("status", {}).get("type", {})
        if status.get("completed") and when < now:
            try:
                hs, ass = int(home["score"]), int(away["score"])
            except (KeyError, ValueError, TypeError):
                continue
            history.setdefault(home_name, []).append({"date": event["date"], "scored": hs, "allowed": ass})
            history.setdefault(away_name, []).append({"date": event["date"], "scored": ass, "allowed": hs})
        elif now < when <= now + dt.timedelta(days=21):
            upcoming.append((when, event, home_name, away_name))
    games = []
    for when, event, home, away in sorted(upcoming, key=lambda item: (item[0], str(item[1].get('id', '')))):
        teams = []
        for name in (away, home):
            logs = sorted((x for x in history.get(name, []) if parse(x["date"]) < when), key=lambda x: x["date"], reverse=True)
            teams.append({"team": name, "sample_size": len(logs), "score_history": logs[:20]})
        games.append({"event_id": str(event["id"]), "event": away + " @ " + home,
                      "commence_time": event["date"], "away": away, "home": home, "teams": teams})
    if not games:
        raise RuntimeError("No future NFL games from ESPN; refusing to overwrite existing feed")
    if not any(len(t["score_history"]) >= 8 for g in games for t in g["teams"]):
        raise RuntimeError("Historical score samples insufficient; refusing to overwrite existing feed")
    payload = {"source": "ESPN public scoreboard", "source_detail": "Scheduled games and completed scoring history only; no verified injuries, starters or sportsbook prices.",
               "generated_from_saved_feeds": False, "source_games_fetched_at": now.isoformat(),
               "market_schedule_source": "espn-scoreboard", "market_prices_not_verified_live": True, "games": games}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print("Published", len(games), "future games, with", len(events), "source events")

if __name__ == "__main__":
    main()
