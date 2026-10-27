#!/usr/bin/env python3
"""Build NFL player game feed from a genuine nflverse player-stats CSV. No fabricated IDs."""
import argparse,csv,json,sys
from collections import defaultdict
from pathlib import Path
FIELDS={"Passing yards":"passing_yards","Passing touchdowns":"passing_tds","Rushing yards":"rushing_yards","Receiving yards":"receiving_yards","Receptions":"receptions","Pass Attempts":"attempts","Completions":"completions","Rush Attempts":"carries","Targets":"targets","Rushing touchdowns":"rushing_tds","Receiving touchdowns":"receiving_tds"}
def build(rows):
    players=defaultdict(lambda:{"games":[]})
    seen=set()
    for n,r in enumerate(rows,2):
        season=str(r.get("season") or "").strip()
        if season not in ("2025","2026") or str(r.get("season_type") or "").strip().upper()!="REG":continue
        player_id=str(r.get("player_id") or "").strip()
        name=str(r.get("player_display_name") or r.get("player_name") or "").strip()
        game_id=str(r.get("game_id") or "").strip()
        week=str(r.get("week") or "").strip()
        if not player_id or not name or not game_id or not week.isdigit() or not 1<=int(week)<=18:
            raise ValueError(f"row {n}: missing stable player/game identity or valid week")
        key=(player_id,game_id)
        if key in seen:raise ValueError(f"row {n}: duplicate player/game {key}")
        seen.add(key)
        values={}
        for label,column in FIELDS.items():
            raw=r.get(column)
            if raw is None or str(raw).strip()=="":
                continue
            try:
                value=float(raw)
            except ValueError as exc:
                raise ValueError(f"row {n}: invalid {column}") from exc
            if not 0<=value<10000:raise ValueError(f"row {n}: out-of-range {column}")
            values[label]=value
        if not values:raise ValueError(f"row {n}: no observed stat values")
        player=players[player_id]
        if player.get("name") and player["name"]!=name:raise ValueError(f"row {n}: conflicting player identity")
        player["name"]=name
        player["player_id"]=player_id
        player["games"].append({"game_id":game_id,"season":int(season),"week":int(week),"season_type":"REG","values":values})
    if not seen:raise ValueError("No valid 2025–26 regular season observations; refusing empty feed")
    return {"source":"nflverse-stats-player-week","source_note":"Observed nflverse CSV; game_id required; no fabricated joins","players":list(players.values())}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True,help="Verified nflverse player_stats CSV")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    with args.input.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        required={"season","season_type","week","player_id","game_id"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise SystemExit("CSV missing mandatory game/player identity columns; refusing to write")
        result=build(reader)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    tmp=args.output.with_suffix(".tmp")
    tmp.write_text(json.dumps(result,separators=(",",":")),encoding="utf-8")
    tmp.replace(args.output)
    print(f"Created {len(result['players'])} player records")
if __name__=="__main__":main()
