#!/usr/bin/env python3
"""UFC training camp and coaching features, strictly as-of pre-fight.
No unverified gym inference or automatic gym 'bonus'.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

def instant(value):
    t=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None:
        raise ValueError("Timezone-aware dates required")
    return t.astimezone(dt.timezone.utc)

def camp_features(rows,as_of):
    cutoff=instant(as_of)
    if not isinstance(rows,list):
        raise ValueError("Camp observations must be list")
    output=[]
    seen=set()
    rejected=0
    for row in rows:
        if not isinstance(row,dict):
            rejected+=1;continue
        try:
            fid=str(row["fight_id"]).strip()
            fighter=str(row["fighter"]).strip()
            gym=str(row["gym"]).strip()
            source=str(row["source_url"]).strip()
            observed=instant(row["verified_at"])
            if not all((fid,fighter,gym,source)) or observed>=cutoff:
                raise ValueError("Unverified or post-cutoff camp information")
            key=(fid,fighter)
            if key in seen:
                raise ValueError("Duplicate fighter-fight camp record")
            days=row.get("camp_days")
            if days is not None and (isinstance(days,bool) or not isinstance(days,int) or not 0<=days<=180):
                raise ValueError("Invalid camp length")
            change=row.get("gym_changed")
            continuity=row.get("head_coach_continuity")
            short=row.get("short_notice")
            for flag in (change,continuity,short):
                if flag is not None and type(flag) is not bool:
                    raise ValueError("Invalid evidence flag")
            seen.add(key)
            output.append({"fight_id":fid,"fighter":fighter,"gym":gym,
                           "camp_days":days,"gym_changed":change,
                           "head_coach_continuity":continuity,"short_notice":short,
                           "verified_at":observed.isoformat(),"source_url":source,
                           "camp_completeness":sum(x is not None for x in (days,change,continuity,short))/4,
                           "research_only":True})
        except (KeyError,ValueError,TypeError,AttributeError):
            rejected+=1
    return {"schema":1,"sport":"UFC","as_of":cutoff.isoformat(),
            "accepted":len(output),"rejected":rejected,"records":output,
            "bet_eligible":False,"gym_advantage_probability":None,
            "limitations":["Gym identity and camp claims require verified pre-fight sources",
                           "Camp length is not training quality; short notice is not automatically disadvantage",
                           "Coaching/gym effects are confounded by fighter selection and opponent strength",
                           "Estimate gym effects only with hierarchical shrinkage and chronological holdout"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--as-of",required=True)
    p.add_argument("--output",default="backtests/reports/ufc_camp_features.json")
    a=p.parse_args()
    result=camp_features(json.loads(Path(a.input).read_text())["camps"],a.as_of)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("UFC verified camp records",result["accepted"])
if __name__=="__main__":main()
