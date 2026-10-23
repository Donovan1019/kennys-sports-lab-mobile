#!/usr/bin/env python3
"""Free ESPN UFC schedule adapter. Never emits betting-ready forecasts or invented odds."""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

ENDPOINT = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"
OUTPUT = Path("feed/ufc_research.json")

def get_json(url=ENDPOINT):
    with urlopen(Request(url, headers={"User-Agent": "KennysSportsLab/1.0 (public schedule research)"}), timeout=20) as response:
        return json.load(response)

def _name(competitor):
    athlete = competitor.get("athlete") or {}
    team = competitor.get("team") or {}
    return (athlete.get("displayName") or competitor.get("displayName") or team.get("displayName") or "").strip()

def parse(payload, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    fights, seen = [], set()
    for event in payload.get("events", []):
        event_name = event.get("name") or event.get("shortName") or "UFC event"
        for competition in event.get("competitions", []):
            fight_id = str(competition.get("id") or "")
            competitors = competition.get("competitors") or []
            if len(competitors) != 2:
                continue
            names = [_name(c) for c in competitors]
            if not all(names) or names[0] == names[1]:
                continue
            date_str = competition.get("date") or event.get("date")
            try:
                start = dt.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if start.tzinfo is None or start.astimezone(dt.timezone.utc) <= now:
                    continue
            except (TypeError, ValueError, AttributeError):
                continue
            if not fight_id or fight_id in seen:
                continue
            seen.add(fight_id)
            rounds = competition.get("scheduledRounds") or competition.get("rounds")
            if not isinstance(rounds, int) or rounds not in (3, 5):
                rounds = None
            fights.append({"id": fight_id, "event": event_name, "red": names[0], "blue": names[1],
                           "start_time": start.isoformat(), "scheduled_rounds": rounds,
                           "source": "ESPN public UFC scoreboard", "bet_eligible": False,
                           "odds_verified": False, "fighter_status_verified": False})
    fights.sort(key=lambda f: (f["start_time"], f["id"]))
    return fights

def main():
    now = dt.datetime.now(dt.timezone.utc)
    try:
        payload = get_json()
        fights = parse(payload, now)
    except Exception as exc:
        raise SystemExit("UFC feed refresh failed; existing file preserved: " + str(exc))
    result = {"schema": 1, "sport": "UFC", "source": "ESPN public UFC scoreboard",
              "generated_at": now.isoformat(), "fights": fights, "fighters": [], "bet_eligible": False,
              "integrity": {"fight_card_only": True, "odds": "UNAVAILABLE", "simulations": "UNAVAILABLE",
                            "fighter_history": "UNAVAILABLE", "event_coverage": "ESPN returned events only; not a complete calendar"}}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, OUTPUT)
    print(f"Saved {len(fights)} future UFC bouts; odds/model predictions remain unavailable")

if __name__ == "__main__":
    main()
