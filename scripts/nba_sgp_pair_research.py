"""Research-only same-game NBA player prop outcome association; no picks."""
import json,math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
SOURCE=Path("feed/nba_player_stats.json")
OUTPUT=Path("feed/nba_sgp_same_game_pair_research.json")
LINES={"Points":19.5,"Rebounds":7.5,"Assists":5.5,"Threes":2.5}
def evaluate(data):
    if not isinstance(data,dict) or data.get("source")!="espn-public-boxscore" or data.get("sport")!="nba":
        raise ValueError("verified NBA player game logs required")
    by_game=defaultdict(list)
    for player in data.get("players",[]):
        if not isinstance(player,dict):continue
        pid=str(player.get("id") or "")
        for g in player.get("games",[]):
            if not isinstance(g,dict):continue
            gid=str(g.get("game_id") or "")
            vals=g.get("values")
            if not pid or not gid or not isinstance(vals,dict):continue
            by_game[gid].append((pid,vals))
    counts=defaultdict(lambda:{"games":0,"both":0,"first":0,"second":0})
    for game,entries in by_game.items():
        unique={}
        for pid,vals in entries:unique[pid]=vals
        entries=sorted(unique.items())
        for i,(pid,a) in enumerate(entries):
            for other,b in entries[i+1:]:
                for market,line in LINES.items():
                    x,y=a.get(market),b.get(market)
                    if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 for v in (x,y)):continue
                    key=market
                    c=counts[key];c["games"]+=1
                    c["first"]+=x>line;c["second"]+=y>line;c["both"]+=(x>line and y>line)
    results={}
    for market,c in counts.items():
        n=c["games"]
        if n<100:continue
        pa=c["first"]/n;pb=c["second"]/n;joint=c["both"]/n
        results[market]={"observed_player_pairs":n,"first_over_rate":round(pa,5),
            "second_over_rate":round(pb,5),"joint_over_rate":round(joint,5),
            "independent_product_reference":round(pa*pb,5),
            "joint_minus_independent":round(joint-pa*pb,5)}
    return {"status":"research_only","promotion_approved":False,
        "method":"historical-same-game-player-pair-association",
        "fixed_reference_lines":LINES,"markets":results,
        "limitations":"All player pairs are pooled, overlapping observations are dependent; role/team/opponent, time and player identity are not controlled. Not predictive, not a correlation parameter, and not a betting recommendation."}
def main():
    result=evaluate(json.loads(SOURCE.read_text()))
    result["generated_at"]=datetime.now(timezone.utc).isoformat()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__":main()
