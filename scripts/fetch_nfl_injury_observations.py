#!/usr/bin/env python3
"""Free ESPN NFL injury observation. Source reports are NOT confirmed actives/inactives."""
import json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
URL="https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"
OUT=Path("feed/nfl_injury_observations.json")
def parse(payload,checked_at):
    groups=payload.get("injuries")
    if not isinstance(groups,list):raise ValueError("Missing ESPN team injury arrays")
    seen=set();rows=[];errors=0
    for team in groups:
        if not isinstance(team,dict) or not isinstance(team.get("injuries"),list):errors+=1;continue
        team_id=str(team.get("id") or "").strip()
        if not team_id:errors+=1;continue
        for item in team["injuries"]:
            if not isinstance(item,dict):errors+=1;continue
            athlete=item.get("athlete")
            if not isinstance(athlete,dict):errors+=1;continue
            name=athlete.get("displayName")
            status=item.get("status")
            date=item.get("date")
            if not all(isinstance(x,str) and x.strip() for x in (name,status,date)):errors+=1;continue
            try:
                observed=datetime.fromisoformat(date.replace("Z","+00:00"))
                if observed.tzinfo is None:raise ValueError("naive")
            except ValueError:errors+=1;continue
            key=(team_id,name.strip().lower(),date,status)
            if key in seen:continue
            seen.add(key)
            rows.append({"team_id":team_id,"team":team.get("displayName"),"player":name.strip(),"status":status.strip(),"reported_at":date,"source":"ESPN injury feed","confirmed_inactive":False,"confirmed_active":False,"usage_adjustment_eligible":False})
    return {"source_url":URL,"checked_at":checked_at,"status":"OBSERVED_UNVERIFIED_FOR_GAME_DAY","verified_player_reports":0,"observed_reports":len(rows),"invalid_records":errors,"injuries":rows,"betting_eligible":False}
def main():
    req=urllib.request.Request(URL,headers={"User-Agent":"KennysSportsLab/1.0"})
    with urllib.request.urlopen(req,timeout=30) as resp:
        data=json.load(resp)
    result=parse(data,datetime.now(timezone.utc).isoformat())
    if not result["observed_reports"]:raise ValueError("No valid injury records; old snapshot retained")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    print("ESPN NFL injury observations",result["observed_reports"],"invalid",result["invalid_records"],"game-day eligibility BLOCKED")
if __name__=="__main__":main()
