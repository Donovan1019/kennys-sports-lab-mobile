#!/usr/bin/env python3
"""No-key NCAA ESPN boxscore import with stable source-scoped player mapping."""
import datetime as dt
import json
import os
import pathlib
import re
import urllib.parse
import urllib.request

HISTORY=pathlib.Path("data/ncaab_espn_history.json")
DEST=pathlib.Path("data/ncaab_player_boxscores.json")
MAP=pathlib.Path("data/ncaab_player_map.json")
BASE="https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?"
HEADERS={"User-Agent":"KennysSportsLab/1.0 (public research cache)","Accept":"application/json"}
def clean(x):
    return re.sub(r"[^a-z0-9]+","",str(x or "").casefold())
def athlete_id(x):
    a=x.get("athlete") or {}
    return str(a.get("id") or x.get("athleteId") or "").strip()
def load(path,default):
    return json.loads(path.read_text()) if path.exists() else default
def parse(summary,event,date):
    teams=(summary.get("boxscore") or {}).get("players") or []
    out=[]
    for group in teams:
        team=group.get("team") or {}
        tid=str(team.get("id") or "")
        if not tid: continue
        for section in group.get("statistics") or []:
            labels=section.get("labels") or []
            for row in section.get("athletes") or []:
                aid=athlete_id(row)
                if not aid: continue
                athlete=row.get("athlete") or {}
                name=str(athlete.get("displayName") or athlete.get("fullName") or "").strip()
                if not name: continue
                stats=row.get("stats") or []
                values={str(k).upper():str(v) for k,v in zip(labels,stats)}
                out.append({"event_id":event,"date":date,"provider":"espn-public","provider_player_id":aid,
                    "canonical_player_id":"espn:"+aid,"team_id":tid,"player_name":name,
                    "position":(athlete.get("position") or {}).get("abbreviation"),
                    "statistics":values})
    return out
def build_map(rows):
    players={}
    conflicts=[]
    for row in rows:
        pid=row["canonical_player_id"]
        obj=players.setdefault(pid,{"provider":"espn","provider_player_id":row["provider_player_id"],"names":[],"team_history":[],"games":0})
        if row["player_name"] not in obj["names"]:obj["names"].append(row["player_name"])
        entry={"team_id":row["team_id"],"season":int(row["date"][:4])+1 if int(row["date"][5:7])>=7 else int(row["date"][:4])}
        if entry not in obj["team_history"]:obj["team_history"].append(entry)
        obj["games"]+=1
    aliases={}
    for pid,obj in players.items():
        for name in obj["names"]:
            key=clean(name)
            aliases.setdefault(key,set()).add(pid)
    unique={key:next(iter(ids)) for key,ids in aliases.items() if len(ids)==1}
    ambiguous={key:sorted(ids) for key,ids in aliases.items() if len(ids)>1}
    return {"provider":"espn-public","schema_version":1,"players":players,"unique_name_aliases":unique,
            "ambiguous_name_aliases":ambiguous,"identity_rule":"Provider player ID is authoritative. Names alone never merge ambiguous identities. Team history is season-scoped."}
def run():
    history=load(HISTORY,{})
    games=history.get("games") or []
    if not games:raise RuntimeError("Historical game IDs unavailable")
    old=load(DEST,{"games_imported":[],"rows":[]})
    imported=set(old.get("games_imported") or [])
    rows=old.get("rows") or []
    budget=max(1,min(int(os.getenv("NCAAB_PLAYER_IMPORT_BATCH","75")),250))
    candidates=[g for g in games if str(g.get("event_id")) not in imported][:budget]
    errors=[]
    for game in candidates:
        eid=str(game["event_id"])
        try:
            req=urllib.request.Request(BASE+urllib.parse.urlencode({"event":eid}),headers=HEADERS)
            with urllib.request.urlopen(req,timeout=25) as resp:summary=json.load(resp)
            parsed=parse(summary,eid,game["date"])
            if not parsed:
                errors.append({"event_id":eid,"reason":"NO_PLAYER_ROWS"})
                continue
            rows.extend(parsed)
            imported.add(eid)
        except Exception as exc:
            errors.append({"event_id":eid,"reason":type(exc).__name__})
    unique={}
    for row in rows:
        key=(row["event_id"],row["canonical_player_id"])
        if key in unique and unique[key]["team_id"]!=row["team_id"]:
            raise ValueError("Player identity conflict within event "+str(key))
        unique[key]=row
    rows=sorted(unique.values(),key=lambda r:(r["date"],r["event_id"],r["canonical_player_id"]))
    mapping=build_map(rows)
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps({"provider":"espn-public","schema_version":1,"fetched_at":stamp,
        "games_imported":sorted(imported),"rows":rows,"errors":errors[:50],
        "research_only":True},separators=(",",":"))+"\n")
    MAP.write_text(json.dumps({**mapping,"generated_at":stamp},separators=(",",":"))+"\n")
    print("Imported games:",len(imported),"player-game rows:",len(rows),"players:",len(mapping["players"]),
          "ambiguous names:",len(mapping["ambiguous_name_aliases"]),"errors:",len(errors))
if __name__=="__main__":run()
