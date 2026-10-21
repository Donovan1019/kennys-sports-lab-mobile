"""Cross-book NBA/NHL moneyline consensus diagnostics, research-only.

Uses captured validated paired odds, never treats consensus as model edge.
"""
import json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from statistics import median

def summarize(archive, now=None, max_snapshot_age=3600):
    now=now or datetime.now(timezone.utc)
    grouped=defaultdict(dict)
    for r in archive.get("quotes",[]):
        try:
            stamp=datetime.fromisoformat(r["captured_at"].replace("Z","+00:00"))
            if stamp.tzinfo is None or stamp>now or (now-stamp).total_seconds()>max_snapshot_age:continue
            p=float(r["home_no_vig"])
            if not 0<p<1 or abs(float(r["away_no_vig"])+p-1)>0.00001:continue
            key=(r["event_id"],r["away"],r["home"])
            book=r["bookmaker"]
            old=grouped[key].get(book)
            if old is None or stamp>old[0]:grouped[key][book]=(stamp,p)
        except (KeyError,ValueError,TypeError,OverflowError):continue
    results=[]
    for (event,away,home),books in grouped.items():
        if len(books)<2:continue
        ps=[p for _,p in books.values()]
        results.append({"event_id":event,"away":away,"home":home,"bookmaker_count":len(books),"home_consensus_no_vig":round(median(ps),6),"home_probability_range_pp":round(100*(max(ps)-min(ps)),3),"highest_quote_age_seconds":round(max((now-t).total_seconds() for t,_ in books.values())),"status":"research_only_not_model_edge"})
    return {"status":"research_only","events_with_2plus_books":len(results),"events":sorted(results,key=lambda r:(-r["home_probability_range_pp"],r["event_id"]))}

def main():
    now=datetime.now(timezone.utc)
    for sport in ("basketball_nba","icehockey_nhl"):
        path=Path(f"feed/{sport}_paired_moneyline_archive.json")
        if not path.exists():continue
        report=summarize(json.loads(path.read_text()),now)
        Path(f"feed/{sport}_market_consensus.json").write_text(json.dumps(report,indent=2)+"\n")
        print(sport,"independent bookmaker consensus events:",report["events_with_2plus_books"])
if __name__=="__main__":main()
