#!/usr/bin/env python3
"""Import public nflverse weekly player stats; no API key or paid service.
Data source: nflverse/nflverse-data stats_player GitHub release.
Only observed regular/postseason weekly stats, never projections.
"""
import csv, io, json, math, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SEASONS=(2025,2026)
URL="https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{year}.csv"
MARKETS={
 "Receiving yards":"receiving_yards",
 "Receptions":"receptions",
 "Rushing yards":"rushing_yards",
 "Passing yards":"passing_yards",
 "Passing touchdowns":"passing_tds",
 "Rushing touchdowns":"rushing_tds",
 "Receiving touchdowns":"receiving_tds",
}
def parse(source):
    reader=csv.DictReader(io.StringIO(source))
    required={"season","week","player_id"}
    columns=set(reader.fieldnames or [])
    name_column=next((x for x in ("player_display_name","player_name") if x in columns),None)
    team_column=next((x for x in ("recent_team","team") if x in columns),None)
    position_column=next((x for x in ("position","position_group") if x in columns),None)
    if not name_column or not team_column or not position_column:
        raise ValueError("Missing player name/team/position column: "+str(sorted(columns)))
    if not required.issubset(columns):
        raise ValueError("nflverse source schema mismatch: "+str(sorted(required-columns)))
    rows=[]
    if not any(col in columns for col in MARKETS.values()):
        raise ValueError("No supported stat columns found")
    for r in reader:
        if r.get("season_type") not in ("REG","POST"):continue
        try:
            year=int(r["season"]);week=int(r["week"])
            values={name:float(r[col]) for name,col in MARKETS.items() if col in columns and r.get(col) not in ("",None)}
            if any(not math.isfinite(v) or v<0 for v in values.values()):continue
        except (ValueError,TypeError,KeyError):
            continue
        if not r.get("player_id") or not r.get(name_column) or not values:continue
        rows.append({"id":r["player_id"],"name":r[name_column],"team":r[team_column],"position":str(r.get(position_column) or "").upper() if position_column else "","season":year,"week":week,"season_type":r["season_type"],"values":values})
    return rows

def fetch(year):
    req=urllib.request.Request(URL.format(year=year),headers={"User-Agent":"KennysSportsLab/1.0"})
    with urllib.request.urlopen(req,timeout=75) as res:
        data=res.read(35_000_000)
        if res.read(1):raise ValueError("Source exceeds safety size limit")
        return data.decode("utf-8-sig")

def main():
    combined=[];failures=[]
    for year in SEASONS:
        try:
            records=parse(fetch(year))
            if not records:raise ValueError("No usable weekly records")
            combined.extend(records)
            print(year,":",len(records),"verified player-week rows")
        except Exception as exc:
            failures.append({"year":year,"reason":type(exc).__name__})
            print(year,": unavailable:",type(exc).__name__,str(exc)[:350])
    if not combined:raise SystemExit("No verified records retrieved; existing snapshot preserved")
    if failures:raise SystemExit("Partial season fetch: refusing mixed-age snapshot; "+str(failures))
    if not any(row["season"]==2026 and row["position"] in ("QB","RB","WR","TE") for row in combined):raise SystemExit("Missing 2026 player positions: refusing unusable snapshot")
    combined.sort(key=lambda r:(r["season"],r["week"],r["season_type"]=="POST"))
    players=defaultdict(lambda:{"name":"","team":"","position":"","games":[]})
    for row in combined:
        p=players[row["id"]];p["name"]=row["name"];p["team"]=row["team"];p["position"]=row["position"] or p["position"]
        p["games"].append({"season":row["season"],"week":row["week"],"season_type":row["season_type"],"values":row["values"]})
    output={"source":"nflverse-stats-player-week","source_url":"https://github.com/nflverse/nflverse-data/releases/tag/stats_player","fetched_at":datetime.now(timezone.utc).isoformat(),"seasons":list(SEASONS),"unavailable_seasons":failures,"players":[{"id":pid,**p} for pid,p in sorted(players.items())]}
    path=Path("feed/nfl_player_stats.json");path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(output,separators=(",",":"))+"\n",encoding="utf-8")
    print("Saved",len(output["players"]),"players")
if __name__=="__main__":main()
