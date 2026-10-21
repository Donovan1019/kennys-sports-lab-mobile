"""Leakage-resistant chronological NHL probability benchmark.

Uses strictly earlier games and a deterministic Poisson/tie model. Does not
replace the incumbent model unless out-of-sample performance is demonstrated.
"""
import json,math
from collections import defaultdict
from pathlib import Path
from scripts.nhl_moneyline_model import home_moneyline_probability

def evaluate(games):
    games=sorted(games,key=lambda g:(g["date"],g.get("event_id","")))
    history=defaultdict(list)
    predictions=[]
    for g in games:
        day=g["date"][:10]
        if day<"2025-10-01":continue
        home,away=g["home"],g["away"]
        hh=[r for r in history[home] if r[0]<day][-40:]
        ah=[r for r in history[away] if r[0]<day][-40:]
        if len(hh)>=12 and len(ah)>=12:
            mean=lambda rows,i:sum(r[i] for r in rows)/len(rows)
            h=(mean(hh,1)+mean(ah,2))/2
            a=(mean(ah,1)+mean(hh,2))/2
            p=home_moneyline_probability(max(.1,a),max(.1,h))
            y=int(g["home_score"]>g["away_score"])
            predictions.append({"date":day,"event_id":g.get("event_id"),"home_probability":round(p,6),"home_won":y,"home_goals":round(h,3),"away_goals":round(a,3)})
        history[home].append((day,g["home_score"],g["away_score"]))
        history[away].append((day,g["away_score"],g["home_score"]))
    if len(predictions)<200:raise ValueError("Insufficient chronological NHL validation data")
    split=int(len(predictions)*.7)
    cutoff=predictions[split]["date"]
    train=[p for p in predictions if p["date"]<cutoff]
    test=[p for p in predictions if p["date"]>=cutoff]
    assert train[-1]["date"]<test[0]["date"]
    brier=lambda rows,key:sum((p[key]-p["home_won"])**2 for p in rows)/len(rows)
    home_rate=sum(p["home_won"] for p in train)/len(train)
    model=brier(test,"home_probability")
    baseline=sum((home_rate-p["home_won"])**2 for p in test)/len(test)
    return {"method":"nhl-strict-prior-day-independent-poisson-ot-proxy","status":"experimental","train_games":len(train),"holdout_games":len(test),"train_end":train[-1]["date"],"holdout_start":test[0]["date"],"holdout_brier":round(model,6),"historical_home_rate_brier":round(baseline,6),"holdout_pass":model<baseline,"limitations":["OT/shootout resolution is a proxy, not independently fitted","Final score data includes OT/SO goals","No verified closing market odds or goalie/lineup adjustments"]}

def main():
    games=json.loads(Path("feed/nhl_completed_games.json").read_text())["games"]
    report=evaluate(games)
    Path("feed/nhl_independent_validation.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
