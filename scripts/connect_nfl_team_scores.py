"""Free ESPN completed NFL score importer; independent of sportsbook odds.
Creates experimental team scoring inputs for Monte Carlo; does not certify forecasts.
"""
import json,math,statistics,urllib.request
from collections import defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path

SCOREBOARD="https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={year}&limit=500"
def parse_scoreboard(payload):
    rows=[]
    for event in payload.get("events",[]):
        comp=(event.get("competitions") or [{}])[0]
        if not comp.get("status",{}).get("type",{}).get("completed",False):continue
        sides=comp.get("competitors",[])
        if len(sides)!=2:continue
        try:
            away=next(x for x in sides if x["homeAway"]=="away")
            home=next(x for x in sides if x["homeAway"]=="home")
            a,h=float(away["score"]),float(home["score"])
            date=datetime.fromisoformat(event["date"].replace("Z","+00:00"))
            if not all(math.isfinite(x) and x>=0 for x in (a,h)):continue
            rows.append({"date":date.isoformat(),"event_id":event.get("id"),"away":away["team"]["displayName"],"home":home["team"]["displayName"],"away_score":a,"home_score":h})
        except (KeyError,ValueError,TypeError,StopIteration):continue
    return rows

def team_parameters(games,team,as_of,limit=12):
    cutoff=datetime.fromisoformat(as_of.replace("Z","+00:00"))
    recent=sorted((g for g in games if datetime.fromisoformat(g["date"])<cutoff and team in (g["away"],g["home"])),key=lambda g:g["date"])[-limit:]
    scored=[g["away_score"] if g["away"]==team else g["home_score"] for g in recent]
    allowed=[g["home_score"] if g["away"]==team else g["away_score"] for g in recent]
    if len(scored)<8:return None
    return {"for_mean":statistics.mean(scored),"against_mean":statistics.mean(allowed),"for_sd":max(3,statistics.stdev(scored)),"against_sd":max(3,statistics.stdev(allowed)),"games":len(scored)}

def assemble(games,odds,as_of,upcoming=None):
    events={}
    for r in odds.get("odds",[]):
        if r.get("sport")!="americanfootball_nfl" or r.get("event_id") in events:continue
        names=(r.get("event") or "").split(" @ ")
        if len(names)!=2:continue
        away,home=names
        if upcoming is not None and (away,home) not in upcoming:continue
        a,h=team_parameters(games,away,as_of),team_parameters(games,home,as_of)
        if a is None or h is None:continue
        events[r["event_id"]]={"event_id":r["event_id"],"sport":"americanfootball_nfl","away_team":away,"home_team":home,
            "away_mean":(a["for_mean"]+h["against_mean"])/2,"home_mean":(h["for_mean"]+a["against_mean"])/2,
            "away_sd":math.sqrt((a["for_sd"]**2+h["against_sd"]**2)/2),"home_sd":math.sqrt((h["for_sd"]**2+a["against_sd"]**2)/2),
            "sample_size":min(a["games"],h["games"]),"as_of":as_of,"validated":True,
            "method":"historical-team-points-scored-allowed","calibration_status":"NOT_BACKTESTED"}
    return {"source":"verified-independent-team-scoring","fetched_at":as_of,"source_detail":"ESPN public completed NFL scoreboards; experimental pregame team scoring distributions","games":list(events.values())}

def main():
    now=datetime.now(timezone.utc).isoformat()
    games=[]
    for year in (datetime.now(timezone.utc).year-1,datetime.now(timezone.utc).year):
        req=urllib.request.Request(SCOREBOARD.format(year=year),headers={"User-Agent":"KennysSportsLab/1.0"})
        with urllib.request.urlopen(req,timeout=45) as res:games.extend(parse_scoreboard(json.load(res)))
    if not games:raise SystemExit("No verified completed games; existing feed preserved")
    games=list({(g["date"],g["away"],g["home"]):g for g in games}.values())
    games.sort(key=lambda g:g["date"])
    Path("feed/nfl_completed_games.json").write_text(json.dumps({"source":"espn-public-completed-nfl-games","fetched_at":now,"games":games},indent=2)+"\n")
    odds=json.loads(Path("feed/americanfootball_nfl.json").read_text())
    # Do not treat a saved odds event as upcoming without a verified future kickoff.
    schedule_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    with urllib.request.urlopen(urllib.request.Request(schedule_url,headers={"User-Agent":"KennysSportsLab/1.0"}),timeout=45) as res:schedule=json.load(res)
    upcoming=set()
    for event in schedule.get("events",[]):
        try:
            kickoff=datetime.fromisoformat(event["date"].replace("Z","+00:00"))
            sides=event["competitions"][0]["competitors"]
            away=next(x["team"]["displayName"] for x in sides if x["homeAway"]=="away")
            home=next(x["team"]["displayName"] for x in sides if x["homeAway"]=="home")
            if kickoff>datetime.fromisoformat(now):upcoming.add((away,home))
        except (KeyError,ValueError,TypeError,StopIteration):continue
    result=assemble(games,odds,now,upcoming=upcoming)
    Path("feed/independent_game_inputs.json").write_text(json.dumps(result,indent=2)+"\n")
    print("Verified completed NFL games:",len(games),"eligible upcoming matchups:",len(result["games"]))
if __name__=="__main__":main()
