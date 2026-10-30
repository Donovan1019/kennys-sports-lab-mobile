#!/usr/bin/env python3
"""Evidence-gated possession simulator. Requires historical team box-score possessions and efficiency.
Does not infer possession inputs from Elo, odds or final W/L results.
"""
import datetime as dt
import hashlib
import json
import math
import pathlib
import random

def metrics(games, now, min_games=15):
    """Use historical games with actual FGA, FTA, ORB, TO and points for both teams."""
    team_rows={}
    for game in games:
        try:
            tip=dt.datetime.fromisoformat(game["date"].replace("Z","+00:00"))
            if tip>=now:continue
            home,away=game["home"],game["away"]
            for team,opp in ((home,away),(away,home)):
                own=game["box"][team];other=game["box"][opp]
                possessions=float(own["fga"])-float(own["orb"])+float(own["turnovers"])+.44*float(own["fta"])
                opp_possessions=float(other["fga"])-float(other["orb"])+float(other["turnovers"])+.44*float(other["fta"])
                points=float(own["points"]);opp_points=float(other["points"])
                if not (70<=possessions<=130 and 70<=opp_possessions<=130 and 50<=points<=200 and 50<=opp_points<=200):continue
                team_rows.setdefault(team,[]).append((tip,possessions,points/possessions,opp_points/opp_possessions))
        except (KeyError,TypeError,ValueError,ZeroDivisionError):continue
    result={}
    for team,rows in team_rows.items():
        rows=sorted(rows,reverse=True)[:30]
        if len(rows)<min_games:continue
        result[team]={"games":len(rows),"pace":sum(r[1] for r in rows)/len(rows),"offense_ppp":sum(r[2] for r in rows)/len(rows),"defense_ppp_allowed":sum(r[3] for r in rows)/len(rows)}
    return result

def simulate(home, away, data, event_id, draws=10000):
    if home not in data or away not in data:return {"status":"unavailable","reason":"historical_box_score_possessions_missing"}
    h=data[home];a=data[away]
    pace=(h["pace"]+a["pace"])/2
    h_ppp=(h["offense_ppp"]+a["defense_ppp_allowed"])/2
    a_ppp=(a["offense_ppp"]+h["defense_ppp_allowed"])/2
    if not (75<=pace<=120 and .7<=h_ppp<=1.5 and .7<=a_ppp<=1.5):return {"status":"unavailable","reason":"implausible_possession_inputs"}
    rng=random.Random(int(hashlib.sha256(event_id.encode()).hexdigest()[:16],16))
    home_wins=0;ties=0;ot_periods=0
    for _ in range(draws):
        possessions=max(70,min(125,round(rng.gauss(pace,5))))
        hs=ascore=0
        for _ in range(possessions):
            # Poisson approximation for points per possession, with independent team offense.
            def points(ppp):
                # Bernoulli points: 0, 2, 3; adjusted to target mean.
                three=min(.18,ppp*.14)
                two=min(.55,max(.05,(ppp-3*three)/2))
                u=rng.random()
                return 3 if u<three else 2 if u<three+two else 0
            hs+=points(h_ppp);ascore+=points(a_ppp)
        if hs==ascore:
            ties+=1
            # Five-minute overtime, approximated as ~5/48 of regulation possessions.
            # Repeat tied overtime periods; independent possession scores remain a limitation.
            for _ot in range(20):
                ot_periods+=1
                ot_possessions=max(1,round(possessions*5/48))
                for _ in range(ot_possessions):
                    hs+=points(h_ppp);ascore+=points(a_ppp)
                if hs!=ascore:break
            if hs==ascore:
                # Extremely rare unresolved ties: reject the simulation instead of fabricating a winner.
                return {"status":"unavailable","reason":"overtime_unresolved"}
        if hs>ascore:home_wins+=1
    return {"status":"diagnostic_only","home":home,"away":away,"draws":draws,"estimated_possessions":round(pace,2),"home_offense_ppp":round(h_ppp,4),"away_offense_ppp":round(a_ppp,4),"home_regulation_win_probability":round(home_wins/draws,5),"regulation_tie_probability":round(ties/draws,5),"home_full_game_win_probability":round(home_wins/draws,5),"overtime_periods_simulated":ot_periods,"overtime_unmodeled":False,"injuries_rest_unmodeled":True,"historical_calibration_unverified":True,"betting_eligible":False}

def main():
    def load(p):
        try:return json.loads(pathlib.Path(p).read_text())
        except (OSError,ValueError):return {}
    now=dt.datetime.now(dt.timezone.utc)
    evidence=load("data/nba_ml_possession_boxscores.json")
    games=evidence.get("games",[])
    data=metrics(games,now)
    odds=load("feed/basketball_nba.json")
    seen=set();results=[]
    for r in odds.get("odds",[]):
        eid=str(r.get("event_id",""))
        names=str(r.get("event","")).split(" @ ")
        if eid in seen or len(names)!=2 or r.get("market")!="h2h":continue
        seen.add(eid)
        results.append({"event_id":eid,**simulate(names[1],names[0],data,eid)})
    report={"status":"diagnostic_only" if data else "unavailable","generated_at":now.isoformat(),"source":"historical team box-score possessions, not Elo or bookmaker odds","qualified_teams":len(data),"games":results,"betting_eligible":False,"blockers":["historical_possession_evidence_and_walkforward_validation_required","overtime_approximation_unvalidated","injury_rest_unverified","parlay_quote_and_correlation_unverified"]}
    target=pathlib.Path("feed/nba_ml_possession_audit.json");target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(report,indent=2)+"\n")
    print(report["status"],len(results),"games",len(data),"qualified teams")
if __name__=="__main__":main()
