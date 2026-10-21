"""Read-only The Odds API adapter. Never stores or prints the API key."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from scripts.paired_moneyline_market import paired_moneylines
from scripts.archive_paired_moneylines import append_snapshot

SPORTS=("basketball_nba","icehockey_nhl","americanfootball_nfl")
def normalize(sport,events):
    rows=[]
    for e in events:
        if not isinstance(e,dict):continue
        away,home=e.get("away_team"),e.get("home_team")
        if not away or not home or not e.get("id") or not e.get("commence_time"):continue
        for book in e.get("bookmakers",[]):
            if not book.get("key"):continue
            for market in book.get("markets",[]):
                if market.get("key")!="h2h":continue
                updated=market.get("last_update") or book.get("last_update")
                for outcome in market.get("outcomes",[]):
                    if outcome.get("name") not in (away,home):continue
                    rows.append({"event_id":e["id"],"event":f"{away} @ {home}","commence_time":e["commence_time"],"updated_at":updated,"bookmaker":book["key"],"market":"h2h","selection":outcome["name"],"price":outcome.get("price")})
    return {"sport":sport,"odds":rows}

def fetch(sport,key):
    url="https://api.the-odds-api.com/v4/sports/"+sport+"/odds/?"+urlencode({"apiKey":key,"regions":"us","markets":"h2h","oddsFormat":"american"})
    with urlopen(Request(url,headers={"User-Agent":"KennysSportsLab/1.0"}),timeout=25) as response:
        data=json.load(response)
        if not isinstance(data,list):raise ValueError("Unexpected odds response")
        return data

def main():
    key=os.environ.get("THE_ODDS_API_KEY")
    if not key:
        print("THE_ODDS_API_KEY missing: no API calls or feed modifications")
        return
    now=datetime.now(timezone.utc)
    for sport in SPORTS:
        try:
            normalized=normalize(sport,fetch(sport,key))
            pairs=paired_moneylines(normalized,now)
            # Avoid overwriting the existing feed with empty or incomplete data.
            if not pairs:
                print(f"{sport}: zero valid paired pregame markets; existing feed unchanged")
                continue
            Path(f"feed/{sport}.json").write_text(json.dumps(normalized,indent=2)+"\n")
            archive_path=Path(f"feed/{sport}_paired_moneyline_archive.json")
            old=json.loads(archive_path.read_text()) if archive_path.exists() else {"quotes":[]}
            archived=append_snapshot(old,normalized,now)
            added=archived.pop("added")
            if added:archive_path.write_text(json.dumps(archived,indent=2)+"\n")
            print(f"{sport}: {len(pairs)} verified fresh pairs; {added} archived")
        except Exception as exc:
            print(f"{sport}: data collection unavailable ({type(exc).__name__}); no unverified prices published")
if __name__=="__main__":main()
