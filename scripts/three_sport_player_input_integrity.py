"""Free-first input integrity report. No paid API calls or betting picks."""
import json
from datetime import datetime, timezone
from pathlib import Path

SPORTS = {
    "NFL": ("americanfootball_nfl", "nfl_player_stats.json"),
    "NBA": ("basketball_nba", "nba_player_stats.json"),
    "NHL": ("icehockey_nhl", "nhl_official_player_stats.json"),
}

def load(path):
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except (OSError, ValueError):
        return {}

def timestamp(value):
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo else None
    except (ValueError, TypeError):
        return None

def assess(now=None, root=Path(".")):
    now = now or datetime.now(timezone.utc)
    result = {"generated_at": now.isoformat(), "status": "research_only", "sports": {}}
    for sport, (slug, history) in SPORTS.items():
        hist = load(root / "feed" / history)
        odds = load(root / "feed" / (slug + ".json"))
        quotes = odds.get("events", [])
        if not isinstance(quotes, list):
            quotes = []
        markets = set()
        latest = None
        for event in quotes:
            if not isinstance(event, dict):
                continue
            for book in event.get("bookmakers", []) or []:
                if not isinstance(book, dict):
                    continue
                for market in book.get("markets", []) or []:
                    if not isinstance(market, dict):
                        continue
                    key = market.get("key")
                    if isinstance(key, str):
                        markets.add(key)
                    dt = timestamp(market.get("last_update") or book.get("last_update"))
                    if dt and (latest is None or dt > latest):
                        latest = dt
        age = (now - latest).total_seconds() / 60 if latest else None
        players = hist.get("players", [])
        result["sports"][sport] = {
            "player_history_present": isinstance(players, list) and len(players) > 0,
            "player_history_count": len(players) if isinstance(players, list) else 0,
            "archived_market_types": sorted(markets),
            "archived_quote_last_update": latest.isoformat() if latest else None,
            "archived_quote_age_minutes": round(age, 1) if age is not None else None,
            "fresh_quote_timestamp_within_60m": age is not None and 0 <= age <= 60,
            "live_event_matched_player_props_verified": False,
            "independent_player_team_and_lineup_verified": False,
            "injury_adjusted_player_projection_validated": False,
            "player_simulation_calibrated": False,
            "verified_betting_recommendations": 0,
            "note": "Historical stats and archived event odds do not establish live player props, confirmed lineups, or betting edges.",
        }
    return result

def main():
    output = assess()
    path = Path("feed/three_sport_player_input_integrity.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print("Player input integrity: " + ", ".join(
        f"{sport}: {v['player_history_count']} historical players; {len(v['archived_market_types'])} archived market types; 0 verified picks"
        for sport, v in output["sports"].items()))

if __name__ == "__main__":
    main()
