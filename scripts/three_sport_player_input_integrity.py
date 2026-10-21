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
        rows = odds.get("odds", [])
        if not isinstance(rows, list):
            rows = []
        markets = set()
        latest = None
        valid_rows = 0
        invalid_rows = 0
        future_event_ids = set()
        books = set()
        stale_rows = 0
        future_dated_rows = 0
        event_metadata = {}
        inconsistent_event_rows = 0
        future_event_market_coverage = {}
        for row in rows:
            if not isinstance(row, dict):
                invalid_rows += 1
                continue
            quote_at = timestamp(row.get("updated_at"))
            event_at = timestamp(row.get("commence_time"))
            price = row.get("price")
            if (not row.get("event_id") or not row.get("bookmaker")
                    or not row.get("market") or not row.get("selection")
                    or not quote_at or not event_at
                    or not isinstance(price, (int, float)) or isinstance(price, bool)
                    or not -100000 <= price <= 100000 or price == 0):
                invalid_rows += 1
                continue
            valid_rows += 1
            if quote_at > now:
                future_dated_rows += 1
            if (now - quote_at).total_seconds() > 3600:
                stale_rows += 1
            identity = (row.get("event"), row.get("commence_time"))
            event_id = row["event_id"]
            if event_id in event_metadata and event_metadata[event_id] != identity:
                inconsistent_event_rows += 1
            else:
                event_metadata[event_id] = identity
            markets.add(row["market"])
            books.add(row["bookmaker"])
            if event_at > now:
                future_event_ids.add(event_id)
                future_event_market_coverage.setdefault(row["market"], set()).add(event_id)
            if latest is None or quote_at > latest:
                latest = quote_at
        age = (now - latest).total_seconds() / 60 if latest else None
        players = hist.get("players", [])
        result["sports"][sport] = {
            "player_history_present": isinstance(players, list) and len(players) > 0,
            "player_history_count": len(players) if isinstance(players, list) else 0,
            "archived_market_types": sorted(markets),
            "archived_quote_rows": len(rows),
            "valid_archived_quote_rows": valid_rows,
            "invalid_archived_quote_rows": invalid_rows,
            "archived_bookmakers": sorted(books),
            "stale_archived_quote_rows_over_60m": stale_rows,
            "future_dated_quote_rows": future_dated_rows,
            "inconsistent_event_metadata_rows": inconsistent_event_rows,
            "upcoming_events_by_market": {market: len(ids) for market, ids in sorted(future_event_market_coverage.items())},
            "future_event_count_with_archived_quotes": len(future_event_ids),
            "archived_quote_last_update": latest.isoformat() if latest else None,
            "archived_quote_age_minutes": round(age, 1) if age is not None else None,
            "fresh_quote_timestamp_within_60m": age is not None and 0 <= age <= 60,
            "fresh_quote_is_not_live_market_verification": True,
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
