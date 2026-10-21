"""Validate paired pregame markets before any price comparison."""
from collections import defaultdict
from scripts.audit_odds_integrity import parse_time
from scripts.betting_market_math import no_vig_two_way

def paired_moneylines(feed,now,max_age_seconds=900):
    groups=defaultdict(dict)
    for row in feed.get("odds",[]):
        if row.get("market")!="h2h" or not row.get("event_id") or not row.get("bookmaker"):continue
        start,updated=parse_time(row.get("commence_time")),parse_time(row.get("updated_at"))
        if not start or not updated or start<=now or updated>now or (now-updated).total_seconds()>max_age_seconds:continue
        teams=str(row.get("event","")).split(" @ ")
        if len(teams)!=2 or row.get("selection") not in teams:continue
        price=row.get("price")
        if isinstance(price,bool) or not isinstance(price,(int,float)) or -100<price<100:continue
        key=(row["event_id"],row["bookmaker"])
        old=groups[key].get(row["selection"])
        if old is None or parse_time(old["updated_at"])<updated:groups[key][row["selection"]]=row
    result=[]
    for (event,book),selections in groups.items():
        if len(selections)!=2:continue
        a,h=next(iter(selections.values()))["event"].split(" @ ")
        if a not in selections or h not in selections:continue
        ar,hr=selections[a],selections[h]
        pa,ph=no_vig_two_way(ar["price"],hr["price"])
        result.append({"event_id":event,"bookmaker":book,"away":a,"home":h,"away_price":ar["price"],"home_price":hr["price"],"away_no_vig":round(pa,6),"home_no_vig":round(ph,6),"quote_age_seconds":round(max((now-parse_time(ar["updated_at"])).total_seconds(),(now-parse_time(hr["updated_at"])).total_seconds()))})
    return result
