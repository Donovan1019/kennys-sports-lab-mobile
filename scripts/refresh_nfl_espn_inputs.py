#!/usr/bin/env python3
"""Fetch fresh independent NFL schedule and completed scoring histories from ESPN."""
import json
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

def parse(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("ESPN timestamp missing timezone")
    return stamp.astimezone(timezone.utc)

def collect(payloads, now):
    histories = defaultdict(dict)
    upcoming = {}
    for payload in payloads:
        for event in payload.get("events", []):
            try:
                game_id = str(event["id"])
                start = parse(event["date"])
                comp = event["competitions"][0]
                teams = comp["competitors"]
                if len(teams) != 2:
                    continue
                by_side = {x["homeAway"]: x for x in teams}
                away, home = (by_side[side]["team"]["displayName"] for side in ("away", "home"))
                if not away or not home:
                    continue
                completed = bool(comp.get("status", event.get("status", {})).get("type", {}).get("completed"))
                if completed and start < now:
                    a, h = float(by_side["away"]["score"]), float(by_side["home"]["score"])
                    if not all(0 <= v <= 100 for v in (a, h)):
                        continue
                    histories[away][game_id] = {"date": start.isoformat(), "season_type": 2, "scored": a, "allowed": h}
                    histories[home][game_id] = {"date": start.isoformat(), "season_type": 2, "scored": h, "allowed": a}
                elif not completed and start > now:
                    upcoming[game_id] = {"event_id": game_id, "event": away + " @ " + home,
                                         "commence_time": start.isoformat(), "away": away, "home": home}
            except (KeyError, ValueError, TypeError, IndexError, AttributeError):
                continue
    games = []
    for game in sorted(upcoming.values(), key=lambda x: x["commence_time"]):
        teams = []
        for name in (game["away"], game["home"]):
            rows = sorted(histories[name].values(), key=lambda x: x["date"], reverse=True)[:8]
            teams.append({"team": name, "sample_size": len(rows), "score_history": rows})
        games.append({**game, "teams": teams})
    return games

def main():
    now = datetime.now(timezone.utc)
    # ESPN regular season weeks; no sportsbook odds or future scores used.
    year = now.year if now.month >= 7 else now.year - 1
    payloads = []
    for week in range(1, 19):
        url = URL + "?dates=" + str(year) + "&seasontype=2&week=" + str(week) + "&limit=100"
        req = urllib.request.Request(url, headers={"User-Agent": "KennySportsLab/1.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            payload = json.load(response)
        if not isinstance(payload.get("events"), list):
            raise ValueError("ESPN returned no valid events list")
        payloads.append(payload)
    games = collect(payloads, now)
    if not games:
        raise ValueError("No upcoming ESPN NFL games; retaining existing inputs")
    output = {"source": "ESPN public scoreboard", "source_games_fetched_at": now.isoformat(),
              "history_season_filter": "regular-season-only", "market_prices_not_verified_live": True,
              "games": games}
    (ROOT / "feed/independent_game_inputs.json").write_text(json.dumps(output, indent=2) + "\n")
    print("NFL ESPN independent inputs:", len(games), "upcoming games")

if __name__ == "__main__":
    main()
