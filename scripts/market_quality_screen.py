"""Fail-closed bookmaker dispersion gate; market agreement is not model edge."""
import json
import math
from pathlib import Path

def screen(archive,consensus,min_books=3,max_range_pp=3.0):
    events=[]
    for e in consensus.get("events",[]):
        n=e.get("bookmaker_count",0)
        spread=e.get("home_probability_range_pp")
        p=e.get("home_consensus_no_vig")
        if type(n)!=int or n<min_books:continue
        if type(p) not in (int,float) or not math.isfinite(p) or not 0<p<1:continue
        if type(spread) not in (int,float) or not math.isfinite(spread) or spread<0:continue
        events.append({"event_id":e["event_id"],"away":e["away"],"home":e["home"],"bookmakers":n,"home_market_probability":p,"market_disagreement_pp":spread,"market_quality":"stable" if spread<=max_range_pp else "dispersed","model_probability":None,"model_market_edge_pp":None,"expected_roi":None,"bet_eligible":False,"reason":"No independent event-matched pregame model prediction"})
    return {"status":"research_only_no_betting_recommendations","minimum_independent_books":min_books,"events_evaluated":len(events),"events":sorted(events,key=lambda x:(x["market_disagreement_pp"],-x["bookmakers"]))}

def main():
    for sport in ("basketball_nba","icehockey_nhl"):
        p=Path(f"feed/{sport}_market_consensus.json")
        if not p.exists():continue
        result=screen(None,json.loads(p.read_text()))
        Path(f"feed/{sport}_market_screen.json").write_text(json.dumps(result,indent=2)+"\n")
        print(sport,"market-quality screened:",result["events_evaluated"],"no model edges asserted")
if __name__=="__main__":main()
