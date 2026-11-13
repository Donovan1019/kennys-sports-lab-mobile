#!/usr/bin/env python3
"""Build safe NFL receiving research context from verified player-week feed.
Third-party sites are discovery/reference sources, not unlicensed scraping feeds.
"""
import collections,datetime,json,pathlib
SOURCES={
 "hashtag_football":{"url":"https://hashtagfootball.com/nfl-target-shares","metrics":["target_share","last_four_target_share"],"mode":"reference"},
 "sumersports":{"url":"https://sumersports.com/players/wide-receiver/","metrics":["routes_run","yprr","adot","epa"],"mode":"reference"},
 "fantasypros":{"url":"https://www.fantasypros.com/nfl/advanced-stats-wr.php","metrics":["yac","adot","catchable_targets"],"mode":"reference"},
 "nfl_savant":{"url":"https://nflsavant.com/","metrics":["target_depth","route_patterns"],"mode":"reference"},
 "nfelo":{"url":"https://www.nfeloapp.com/","metrics":["epa_per_target","catch_rate"],"mode":"reference"}
}
def calculate(rows):
    groups=collections.defaultdict(list)
    for r in rows:
        if r.get("player_id") and r.get("team") and r.get("week") is not None:
            groups[(str(r["player_id"]),str(r["team"]))].append(r)
    output=[]
    for (pid,team),games in sorted(groups.items()):
        games.sort(key=lambda g:(int(g.get("season") or 0),int(g.get("week") or 0)),reverse=True)
        latest=games[0]; last=games[:4]
        def share(rs):
            if not rs or any(x.get("targets") is None or x.get("team_targets") is None for x in rs):return None
            denominator=sum(float(x["team_targets"]) for x in rs)
            return round(100*sum(float(x["targets"]) for x in rs)/denominator,2) if denominator>0 else None
        season=share(games); l4=share(last)
        output.append({"player_id":pid,"player_name":latest.get("player_name"),"team":team,"position":latest.get("position"),"season_target_share":season,"last_four_target_share":l4,"target_share_change_pp":round(l4-season,2) if l4 is not None and season is not None else None,"games_in_l4":len(last)})
    return output
def main():
    source=pathlib.Path("feed/nfl_wr_opportunity.json")
    data=json.loads(source.read_text())
    rows=data.get("games",[])
    if not rows:raise SystemExit("No verified opportunity feed")
    output={"season":data.get("season"),"generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"sources":SOURCES,"source_policy":"Reference links only; do not ingest or claim third-party charting without authorized structured export and verified player ID mapping.","players":calculate(rows)}
    dest=pathlib.Path("feed/nfl_wr_source_context.json")
    dest.write_text(json.dumps(output,separators=(",",":"))+"\n")
    print("Built",len(output["players"]),"verified player trend rows; 5 reference sources registered")
if __name__=="__main__":main()
