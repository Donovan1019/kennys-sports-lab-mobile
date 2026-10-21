"""Audit player betting recommendation readiness without inventing selections or consuming paid APIs."""
import json
from datetime import datetime, timezone
from pathlib import Path

SPORTS={"NFL":"americanfootball_nfl","NBA":"basketball_nba","NHL":"icehockey_nhl"}
REQUIRED=("bet_eligible","status","verified_market","simulation_verified","lineup_verified","market_fresh","is_player_prop","player","market","selection","point","hit_probability","market_odds_american","expected_value","verified_at")
def audit(feed):
    missing=[]
    for field in REQUIRED:
        if field not in feed:missing.append(field)
    if feed.get("bet_eligible") is not True:missing.append("bet_eligible_true")
    if feed.get("status")!="verified":missing.append("status_verified")
    for field in ("verified_market","simulation_verified","lineup_verified","market_fresh","is_player_prop"):
        if feed.get(field) is not True:missing.append(field+"_true")
    for field in ("player","market","selection"):
        if not isinstance(feed.get(field),str) or not feed[field].strip():missing.append(field+"_value")
    for field in ("point","hit_probability","market_odds_american","expected_value"):
        if isinstance(feed.get(field),bool) or not isinstance(feed.get(field),(float,int)):missing.append(field+"_numeric")
    return sorted(set(missing))
def main():
    now=datetime.now(timezone.utc).isoformat()
    output={"generated_at":now,"status":"research_only_until_verified","sports":{}}
    for sport,slug in SPORTS.items():
        path=Path("feed")/(slug+"_pregame_research.json")
        data=json.loads(path.read_text()) if path.exists() else {}
        events=data.get("events",[])
        counts={}
        for e in events:
            for field in audit(e):
                counts[field]=counts.get(field,0)+1
        output["sports"][sport]={"researched_events":len(events),"fully_verified_player_recommendations":0,"missing_field_counts":counts,"note":"Event-level pregame research does not establish verified player-specific props; no betting selections issued."}
    path=Path("feed/player_recommendation_readiness.json")
    path.write_text(json.dumps(output,indent=2)+"\n")
    print("Player recommendation audit: "+", ".join(f"{k} {v['researched_events']} events, 0 verified props" for k,v in output["sports"].items()))
if __name__=="__main__":main()
