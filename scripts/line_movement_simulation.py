"""Independent score simulation using strictly prior completed game history."""
from statistics import mean,stdev
from scripts.sport_simulation import simulate_sport
from scripts.line_movement_research import parse
from scripts.three_sport_backtest import normalize_team
def simulate(sport,row,games,cutoff):
    if sport not in ("basketball_nba","americanfootball_nfl","icehockey_nhl","basketball_ncaab","basketball_wnba"):
        return {"status":"UNAVAILABLE","reason":"No supported team score simulator"}
    histories={}
    for side in ("away","home"):
        name=normalize_team(row[side])
        seen={}
        for g in games:
            t=parse(g.get("commence_time") or g.get("date"))
            if not t or t.date()>=cutoff.date():continue
            if g.get("completed") is not True:continue
            a,h=g.get("away_score"),g.get("home_score")
            if type(a) is not int or type(h) is not int or min(a,h)<0:continue
            if normalize_team(g.get("home"))==name:pair=(h,a)
            elif normalize_team(g.get("away"))==name:pair=(a,h)
            else:continue
            key=(t,normalize_team(g.get("away")),normalize_team(g.get("home")))
            if key in seen and seen[key]!=pair:return {"status":"UNAVAILABLE","reason":"Conflicting historical results"}
            seen[key]=pair
        histories[side]=[v for k,v in sorted(seen.items())][-30:]
    a,h=histories["away"],histories["home"]
    if min(len(a),len(h))<12:return {"status":"UNAVAILABLE","reason":"Fewer than 12 prior completed games per team","away_games":len(a),"home_games":len(h)}
    am=(mean(x[0] for x in a)+mean(x[1] for x in h))/2
    hm=(mean(x[0] for x in h)+mean(x[1] for x in a))/2
    sd=lambda x,y:max(.1,(stdev(v[0] for v in x)+stdev(v[1] for v in y))/2)
    scores=simulate_sport(sport,am,hm,sd(a,h),sd(h,a),trials=10000,seed=str(row["event_id"]))
    n=len(scores)
    return {"status":"INDEPENDENT_SCORE_RESEARCH_ONLY","trials":n,"home_win_probability":sum(h>a for a,h in scores)/n,"away_win_probability":sum(a>h for a,h in scores)/n,"tie_probability":sum(a==h for a,h in scores)/n,"projected_away_score":mean(a for a,h in scores),"projected_home_score":mean(h for a,h in scores),"projected_total":mean(a+h for a,h in scores),"away_games":len(a),"home_games":len(h),"cutoff":cutoff.isoformat(),"bet_eligible":False}
