"""Leakage-safe line movement research from archived sportsbook quotes.

Compares earliest and latest captured snapshots per event/bookmaker; never
labels a quote 'closing' without verified pregame event start timestamps.
"""
import json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

def parse(value):
    try:
        t=datetime.fromisoformat(value.replace("Z","+00:00"))
        return t if t.tzinfo else None
    except (TypeError,ValueError,AttributeError):return None

def movement(archive):
    groups=defaultdict(list)
    for r in archive.get("quotes",[]):
        stamp=parse(r.get("captured_at"))
        p=r.get("home_no_vig")
        if not stamp or type(p) not in (int,float) or not 0<p<1:continue
        if not all(r.get(k) for k in ("event_id","bookmaker","home","away")):continue
        groups[(r["event_id"],r["bookmaker"],r["away"],r["home"])].append((stamp,p))
    changes=[]
    for (event,book,away,home),rows in groups.items():
        rows.sort()
        if len({t for t,_ in rows})<2:continue
        first,last=rows[0],rows[-1]
        changes.append({"event_id":event,"bookmaker":book,"away":away,"home":home,"first_captured_at":first[0].isoformat(),"latest_captured_at":last[0].isoformat(),"first_home_no_vig":first[1],"latest_home_no_vig":last[1],"home_probability_change_pp":round(100*(last[1]-first[1]),3),"is_verified_closing_line":False})
    return {"status":"research_only_not_closing_line_value","paired_bookmaker_series":len(changes),"series":sorted(changes,key=lambda x:(-abs(x["home_probability_change_pp"]),x["event_id"],x["bookmaker"]))}

def main():
    for sport in ("basketball_nba","icehockey_nhl","americanfootball_nfl"):
        src=Path(f"feed/{sport}_paired_moneyline_archive.json")
        if not src.exists():continue
        report=movement(json.loads(src.read_text()))
        Path(f"feed/{sport}_line_movement.json").write_text(json.dumps(report,indent=2)+"\n")
        print(sport,"multi-snapshot bookmaker series:",report["paired_bookmaker_series"])
if __name__=="__main__":main()
