#!/usr/bin/env python3
"""Import settled UFC fights and reported *pre-bout* features from public historical CSV.

This is a RETROSPECTIVE research dataset, not a verified contemporaneous snapshot.
Never certify point-in-time lineage from historical feature column names alone.
"""
import argparse,csv,hashlib,io,json,re
from datetime import date
from pathlib import Path
from urllib.request import Request,urlopen

SOURCE="https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2026/2026-07-07/ultimate_ufc_dataset.csv"
FEATURES=("wins","losses","total_rounds_fought","avg_sig_str_landed","avg_td_landed",
          "avg_sub_att","win_by_ko_tko","win_by_submission","age","reach_cms")
def number(raw):
    if raw is None or not str(raw).strip() or str(raw).strip().lower() in ("na","nan","null"):return None
    try:
        x=float(raw)
        if not (-1e6<x<1e6):return None
        return x
    except ValueError:return None
def transform(rows,source_hash):
    result=[];seen=set();skipped=0
    for r in rows:
        red=(r.get("r_fighter") or "").strip()
        blue=(r.get("b_fighter") or "").strip()
        when=(r.get("date") or "").strip()[:10]
        winner=(r.get("winner") or "").strip().lower()
        if not red or not blue or red==blue or winner not in ("red","blue"):
            skipped+=1;continue
        try:date.fromisoformat(when)
        except ValueError:skipped+=1;continue
        # Stable source-local composite, never assumed equal to UFCStats fight_id.
        key="|".join((when,red.casefold(),blue.casefold()))
        if key in seen:raise ValueError("duplicate fight identity "+key)
        seen.add(key)
        feature={corner:{name:number(r.get(corner+"_"+name)) for name in FEATURES} for corner in ("r","b")}
        rounds=number(r.get("no_of_rounds"))
        if rounds not in (3,5):rounds=None
        result.append({"fight_id":"tidytuesday:"+hashlib.sha256(key.encode()).hexdigest()[:20],
            "date":when,"red":red,"blue":blue,"red_won":int(winner=="red"),
            "scheduled_rounds":rounds,"prebout_features_claimed":feature})
    if not result:raise ValueError("no settled fights")
    return {"source":SOURCE,"source_sha256":source_hash,"provenance":"RETROSPECTIVE_NOT_PIT_CERTIFIED",
            "bet_eligible":False,"training_pit_certified":False,"count":len(result),
            "skipped":skipped,"fights":sorted(result,key=lambda x:(x["date"],x["fight_id"]))}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default=SOURCE)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.source.startswith("https://"):
        if a.source!=SOURCE:raise ValueError("unapproved source")
        with urlopen(Request(a.source,headers={"User-Agent":"KennysSportsLab/1.0"}),timeout=50) as resp:
            raw=resp.read(30_000_000)
    else:raw=Path(a.source).read_bytes()
    payload=transform(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))),hashlib.sha256(raw).hexdigest())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(payload,separators=(",",":"),ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in payload.items() if k!="fights"},indent=2))
if __name__=="__main__":main()
