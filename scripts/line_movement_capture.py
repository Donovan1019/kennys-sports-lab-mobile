"""Capture observed pregame core markets; never reconstruct historical quotes."""
import json, math
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import defaultdict
from scripts.line_movement_research import parse
def capture(data, now):
    fetched=parse(data.get("fetched_at"))
    if data.get("status")!="ok" or not fetched or not now-timedelta(hours=8)<=fetched<=now:return []
    groups=defaultdict(list)
    for r in data.get("odds",[]):
        start,updated=parse(r.get("commence_time")),parse(r.get("updated_at"))
        if not start or not updated or not now<start or not fetched-timedelta(hours=8)<=updated<=fetched:continue
        if r.get("market") not in ("h2h","spreads","totals") or not all(r.get(k) for k in ("event_id","event","bookmaker","selection")):continue
        p=r.get("price")
        if type(p) not in (int,float) or not math.isfinite(p) or abs(p)<100:continue
        groups[(str(r["event_id"]),r["event"],r["bookmaker"],r["market"],start.isoformat())].append(r)
    out=[]
    for (eid,event,book,market,start),rs in groups.items():
        if event.count(" @ ")!=1:continue
        away,home=event.split(" @ ")
        sides=(home,away) if market!="totals" else ("Over","Under")
        if len(rs)!=2 or {r["selection"] for r in rs}!=set(sides):continue
        a,b=(next(r for r in rs if r["selection"]==s) for s in sides)
        point=a.get("point")
        if market!="h2h":
            q=b.get("point")
            if type(point) not in (int,float) or type(q) not in (int,float) or not math.isfinite(point) or not math.isfinite(q) or (point!=-q if market=="spreads" else point!=q):continue
        def implied(p):return -p/(100-p) if p<0 else 100/(100+p)
        pa,pb=implied(a["price"]),implied(b["price"])
        out.append(dict(event_id=eid,home=home,away=away,bookmaker=book,market=market,event_start=start,captured_at=fetched.isoformat(),point=point,home_no_vig=pa/(pa+pb),source=data.get("source"),first_price=a["price"],second_price=b["price"]))
    return out
def main():
    for sport in ("basketball_nba","americanfootball_nfl","icehockey_nhl","basketball_ncaab","basketball_wnba","mma_mixed_martial_arts"):
        src=Path("feed")/(sport+".json")
        if not src.exists():continue
        dest=Path("feed")/(sport+"_core_movement_archive.json")
        old=json.loads(dest.read_text()).get("quotes",[]) if dest.exists() else []
        new=capture(json.loads(src.read_text()),datetime.now(timezone.utc))
        rows={json.dumps(r,sort_keys=True):r for r in old+new}
        dest.write_text(json.dumps({"quotes":list(rows.values())},indent=2)+"\n")
        print(sport,"captured",len(new),"core market pairs")
if __name__=="__main__":main()
