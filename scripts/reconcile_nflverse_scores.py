#!/usr/bin/env python3
"""Independent NFL completed-game score reconciliation against nflverse schedule releases.

Read-only verification: never overwrite ESPN stats or infer player-level data.
"""
import csv
import io
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
URL="https://github.com/nflverse/nfldata/raw/master/data/games.csv"
ALIASES={"Arizona Cardinals":"ARI","Atlanta Falcons":"ATL","Baltimore Ravens":"BAL","Buffalo Bills":"BUF","Carolina Panthers":"CAR","Chicago Bears":"CHI","Cincinnati Bengals":"CIN","Cleveland Browns":"CLE","Dallas Cowboys":"DAL","Denver Broncos":"DEN","Detroit Lions":"DET","Green Bay Packers":"GB","Houston Texans":"HOU","Indianapolis Colts":"IND","Jacksonville Jaguars":"JAX","Kansas City Chiefs":"KC","Las Vegas Raiders":"LV","Los Angeles Chargers":"LAC","Los Angeles Rams":"LA","Miami Dolphins":"MIA","Minnesota Vikings":"MIN","New England Patriots":"NE","New Orleans Saints":"NO","New York Giants":"NYG","New York Jets":"NYJ","Philadelphia Eagles":"PHI","Pittsburgh Steelers":"PIT","San Francisco 49ers":"SF","Seattle Seahawks":"SEA","Tampa Bay Buccaneers":"TB","Tennessee Titans":"TEN","Washington Commanders":"WAS"}
def reconcile(local,external):
    index={}
    for row in external:
        try:
            if row.get("home_score","")=="" or row.get("away_score","")=="":
                continue
            key=(int(row["season"]),row["home_team"],row["away_team"])
            index[key]=(int(float(row["home_score"])),int(float(row["away_score"])))
        except (ValueError,KeyError,TypeError):
            continue
    matched=0;missing=0;discrepancies=[];unmapped=[]
    for game in local:
        date=datetime.fromisoformat(game["date"].replace("Z","+00:00"))
        # January/February games belong to the previous NFL season.
        season=date.year-(1 if date.month<=2 else 0)
        home=ALIASES.get(game["home"]);away=ALIASES.get(game["away"])
        if not home or not away:
            unmapped.append(game.get("event_id"));continue
        scores=index.get((season,home,away))
        if scores is None:
            missing+=1;continue
        matched+=1
        actual=(int(game["home_score"]),int(game["away_score"]))
        if actual!=scores:
            discrepancies.append({"event_id":game["event_id"],"event":game["away"]+" @ "+game["home"],"espn":actual,"nflverse":scores})
    return {"matched":matched,"unmatched":missing,"unmapped":unmapped,"discrepancies":discrepancies}

def main():
    local=json.loads((ROOT/"feed/nfl_completed_games.json").read_text())["games"]
    request=urllib.request.Request(URL,headers={"User-Agent":"KennysSportsLab/1.0"})
    with urllib.request.urlopen(request,timeout=35) as response:
        rows=list(csv.DictReader(io.StringIO(response.read().decode("utf-8-sig"))))
    result=reconcile(local,rows)
    result.update({"source":"nflverse-nfldata-games","source_url":URL,"generated_at":datetime.now(timezone.utc).isoformat(),"total_espn_games":len(local)})
    out=ROOT/"feed/nfl_independent_score_audit.json"
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("Independent score reconciliation:",result["matched"],"matched,",result["unmatched"],"unmatched,",len(result["discrepancies"]),"discrepancies")
    if result["matched"]<20 or result["discrepancies"] or result["unmapped"]:
        raise SystemExit("Score reconciliation failed; report saved locally; not published")

if __name__=="__main__":
    main()
