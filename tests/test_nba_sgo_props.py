import sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "scripts")
from fetch_nba_sgo_props import normalize
now=datetime.now(timezone.utc)
t=now.isoformat()
event={"leagueID":"NBA","eventID":"test-event","status":{"startsAt":(now+timedelta(hours=3)).isoformat()},"players":{"player-1":{"names":{"display":"Example Player"}}},"odds":{"points-player-1-game-ou-over":{"statID":"points","statEntityID":"player-1","periodID":"game","betTypeID":"ou","sideID":"over","byBookmaker":{"draftkings":{"available":True,"odds":"-150","overUnder":"24.5","lastUpdatedAt":t,"altLines":[{"available":True,"odds":"-320","overUnder":"19.5","lastUpdatedAt":t}]}}}}}
rows=normalize({"success":True,"data":[event]},now)
assert len(rows)==2,rows
assert {(r["market"],r["point"]) for r in rows}=={("player_points",24.5),("player_points_alternate",19.5)}
assert all(r["player"]=="Example Player" for r in rows)
event["status"]["started"]=True
assert not normalize({"success":True,"data":[event]},now)
print("SportsGameOdds NBA props normalizer PASS")
