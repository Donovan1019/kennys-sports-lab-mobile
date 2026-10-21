"""Archive verified pregame two-sided sportsbook quotes without inventing prices.

Input snapshots must already be supplied by an authorized data collector.
Archives are research-only; no historical closing-line or EV claims.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from scripts.paired_moneyline_market import paired_moneylines

def append_snapshot(archive, feed, now):
    existing=archive.get("quotes",[])
    new=paired_moneylines(feed,now)
    keyed={}
    for row in existing:
        if all(k in row for k in ("event_id","bookmaker","captured_at")):
            keyed[(row["event_id"],row["bookmaker"],row["captured_at"])]=row
    stamp=now.astimezone(timezone.utc).isoformat()
    for row in new:
        record={**row,"captured_at":stamp,"sport":feed.get("sport"),"source":"validated_snapshot"}
        keyed[(row["event_id"],row["bookmaker"],stamp)]=record
    result=sorted(keyed.values(),key=lambda x:(x["captured_at"],x["event_id"],x["bookmaker"]))
    return {"status":"research_only","quotes":result,"added":len(result)-len(existing)}

def main():
    now=datetime.now(timezone.utc)
    for sport in ("basketball_nba","icehockey_nhl"):
        src=Path(f"feed/{sport}.json")
        if not src.exists():continue
        dst=Path(f"feed/{sport}_paired_moneyline_archive.json")
        archive=json.loads(dst.read_text()) if dst.exists() else {"quotes":[]}
        result=append_snapshot(archive,json.loads(src.read_text()),now)
        added=result.pop("added")
        if added:
            dst.write_text(json.dumps(result,indent=2)+"\n")
        print(f"{sport}: archived {added} new paired quotes (total {len(result['quotes'])})")

if __name__=="__main__":main()
