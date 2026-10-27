#!/usr/bin/env python3
"""Audit NFL historical feed integrity; never synthesize absent data."""
import json
import sys
from pathlib import Path

def inspect(path):
    result={"path":str(path),"status":"BLOCKED","betting_eligible":False,"player_count":0,
            "game_count":0,"event_id_coverage":0,"missing_values":0,"duplicate_player_events":0,
            "issues":[]}
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError) as exc:
        result["issues"].append("missing_or_invalid_json: "+str(exc))
        return result
    if not isinstance(data,dict) or data.get("source")!="nflverse-stats-player-week":
        result["issues"].append("missing_or_unexpected_source")
        return result
    players=data.get("players")
    if not isinstance(players,list) or not players:
        result["issues"].append("no_player_records")
        return result
    seen=set()
    for player in players:
        if not isinstance(player,dict):
            result["issues"].append("malformed_player_record")
            continue
        result["player_count"]+=1
        games=player.get("games")
        if not isinstance(games,list):
            result["issues"].append("missing_games_array")
            continue
        for game in games:
            if not isinstance(game,dict):
                result["issues"].append("malformed_game_record")
                continue
            result["game_count"]+=1
            event=game.get("game_id") or game.get("event_id")
            if event:
                result["event_id_coverage"]+=1
                key=(player.get("player_id") or player.get("name"),str(event))
                if key in seen:result["duplicate_player_events"]+=1
                seen.add(key)
            values=game.get("values")
            if not isinstance(values,dict) or not values:
                result["missing_values"]+=1
    if result["game_count"]==0:result["issues"].append("no_game_records")
    if result["event_id_coverage"]!=result["game_count"]:result["issues"].append("missing_game_ids")
    if result["missing_values"]:result["issues"].append("missing_stat_values")
    if result["duplicate_player_events"]:result["issues"].append("duplicate_player_game_ids")
    if not result["issues"]:result["status"]="DATA_PRESENT_UNVERIFIED"
    return result

if __name__=="__main__":
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path("feed/nfl_player_stats.json")
    print(json.dumps(inspect(path),indent=2,sort_keys=True))
