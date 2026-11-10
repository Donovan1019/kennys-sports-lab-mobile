#!/usr/bin/env python3
"""Fail-closed identity and historical NCAA player boxscore integrity checks."""
import collections
import datetime as dt
import json
import pathlib

ROOT=pathlib.Path("data")
def main():
    d=json.loads((ROOT/"ncaab_player_boxscores.json").read_text())
    m=json.loads((ROOT/"ncaab_player_map.json").read_text())
    h=json.loads((ROOT/"ncaab_espn_history.json").read_text())
    rows=d.get("rows") or []
    players=m.get("players") or {}
    history={str(g["event_id"]):g for g in h.get("games") or []}
    issues=[]
    seen=set()
    coverage=collections.Counter()
    for r in rows:
        pid=r.get("canonical_player_id")
        eid=str(r.get("event_id") or "")
        key=(eid,pid)
        if key in seen:issues.append("DUPLICATE_PLAYER_EVENT:"+eid+":"+str(pid))
        seen.add(key)
        if not pid or pid!="espn:"+str(r.get("provider_player_id") or ""):issues.append("INVALID_PROVIDER_ID:"+eid)
        if pid not in players:issues.append("UNMAPPED_PLAYER:"+str(pid))
        if eid not in history:issues.append("UNKNOWN_GAME:"+eid)
        else:
            game=history[eid]
            if r.get("date")!=game.get("date"):issues.append("GAME_DATE_MISMATCH:"+eid)
            if str(r.get("team_id")) not in {str(t.get("id")) for t in game.get("teams") or []}:issues.append("GAME_TEAM_MISMATCH:"+eid+":"+str(r.get("team_id")))
        if eid:coverage[eid]+=1
    aliases=m.get("unique_name_aliases") or {}
    ambiguous=m.get("ambiguous_name_aliases") or {}
    if set(aliases)&set(ambiguous):issues.append("AMBIGUOUS_ALIAS_EXPOSED_AS_UNIQUE")
    for name,ids in ambiguous.items():
        if len(set(ids))<2:issues.append("INVALID_AMBIGUITY:"+name)
        if any(pid not in players for pid in ids):issues.append("AMBIGUITY_UNMAPPED:"+name)
    for alias,pid in aliases.items():
        if pid not in players:issues.append("ALIAS_UNMAPPED:"+alias)
    result={"generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider":"espn-public","status":"PASS" if not issues else "FAIL",
        "historical_games":len(history),"imported_games":len(d.get("games_imported") or []),
        "player_game_rows":len(rows),"mapped_players":len(players),
        "ambiguous_name_aliases":len(ambiguous),"game_coverage":len(coverage),
        "errors":issues[:50],"research_only":True}
    (ROOT/"ncaab_player_integrity.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if issues:raise SystemExit("NCAA player mapping integrity failed: "+str(len(issues))+" issues")
if __name__=="__main__":main()
