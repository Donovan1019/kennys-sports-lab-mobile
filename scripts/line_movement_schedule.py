import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from zoneinfo import ZoneInfo
from scripts.line_movement_research import parse
from scripts.three_sport_backtest import normalize_team
LEAGUES={"basketball_nba":"basketball/nba","americanfootball_nfl":"football/nfl","icehockey_nhl":"hockey/nhl","basketball_ncaab":"basketball/mens-college-basketball","basketball_wnba":"basketball/wnba"}
def college_history():
    p=Path("data/ncaab_espn_history.json")
    out=[]
    if not p.exists() or not p.stat().st_size:return out
    for g in json.loads(p.read_text()).get("games",[]):
        teams={t.get("homeAway"):t for t in g.get("teams",[])}
        if not all(k in teams for k in ("home","away")):continue
        h,a=teams["home"],teams["away"]
        if not all(type(t.get("points")) in (int,float) and t["points"]>=0 and int(t["points"])==t["points"] and t.get("name") for t in (h,a)):continue
        out.append(dict(event_id=g["event_id"],commence_time=g["date"]+"T12:00:00-05:00",home=h["name"],away=a["name"],home_score=int(h["points"]),away_score=int(a["points"]),completed=True))
    return out
def college_scoreboard_history(now):
    from urllib.parse import urlencode
    out=[]
    # Completed scores only; no expensive per-game boxscore calls.
    for start,end in [(now.date()-timedelta(days=35),now.date()-timedelta(days=1)),(now.date()-timedelta(days=365),now.date()-timedelta(days=330))]:
        for i in range((end-start).days+1):
            day=start+timedelta(days=i)
            url="https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?"+urlencode({"dates":day.strftime("%Y%m%d"),"groups":50,"limit":500})
            try:
                with urlopen(Request(url,headers={"User-Agent":"KSL research"}),timeout=10) as r:data=json.load(r)
                for e in data.get("events",[]):
                    if e.get("status",{}).get("type",{}).get("completed") is not True:continue
                    cs=e.get("competitions") or []
                    if not cs:continue
                    sides={x.get("homeAway"):x for x in cs[0].get("competitors",[])}
                    h,a=sides["home"],sides["away"]
                    out.append(dict(event_id=str(e["id"]),commence_time=e["date"],home=h["team"]["displayName"],away=a["team"]["displayName"],home_score=int(h["score"]),away_score=int(a["score"]),completed=True))
            except (OSError,ValueError,KeyError,TypeError):continue
    return out
def schedule(sport,now):
    if sport not in LEAGUES:return [],"UNSUPPORTED"
    day=now.astimezone(ZoneInfo("America/New_York")).date()
    events={}
    failures=[]
    for offset in range(8):
        date=(day+timedelta(days=offset)).strftime("%Y%m%d")
        url="https://site.api.espn.com/apis/site/v2/sports/"+LEAGUES[sport]+"/scoreboard?dates="+date+"&limit=500"
        if sport=="basketball_ncaab":url+="&groups=50"
        try:
            with urlopen(Request(url,headers={"User-Agent":"KSL-Backtest/1.0"}),timeout=15) as r:data=json.load(r)
            if not isinstance(data.get("events"),list):raise ValueError("Missing events")
            for e in data["events"]:events[str(e["id"])]=e
        except Exception as e:
            failures.append(str(getattr(e,"code",type(e).__name__)))
    if failures:return [],"UNAVAILABLE: incomplete daily schedule "+",".join(failures)
    data={"events":list(events.values())}
    out=[]
    for e in data["events"]:
        t=parse(e.get("date"))
        if not t or t<=now or e.get("status",{}).get("type",{}).get("state")!="pre":continue
        cs=e.get("competitions") or []
        if not cs:continue
        sides={c.get("homeAway"):c.get("team",{}).get("displayName") for c in cs[0].get("competitors",[])}
        if not sides.get("home") or not sides.get("away"):continue
        out.append(dict(event_id="espn-"+str(e["id"]),home=sides["home"],away=sides["away"],event_start=t.isoformat(),bookmakers=0,median_change_pp=None,schedule_source="ESPN scoreboard"))
    return out,"OK"
def join_schedule(rows,fixtures,simulate,sport,games,now):
    out=[]
    for f in fixtures:
        matches=[r for r in rows if all(normalize_team(r[k])==normalize_team(f[k]) for k in ("home","away")) and abs((parse(r["event_start"])-parse(f["event_start"])).total_seconds())<=1800]
        if len(matches)==1:
            out.append(dict(matches[0],schedule_source=f["schedule_source"],odds_status="AVAILABLE"))
        else:
            out.append(dict(f,odds_status="UNAVAILABLE",score_simulation=simulate(sport,f,games,now)))
    return out
