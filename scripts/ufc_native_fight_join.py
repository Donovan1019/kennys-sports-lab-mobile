#!/usr/bin/env python3
"""Strict UFCStats fight-ID join for nlbair fight-level records.

Only native UFCStats fight IDs are accepted. Never join on fighter names, card
position, dates, or row ordering. Retrospective records are not PIT certified.
"""
import argparse,csv,hashlib,io,json,re
from pathlib import Path
from urllib.request import Request,urlopen

BASE="https://raw.githubusercontent.com/nlbair/ufc-data/main/data/"
HEX=re.compile(r"^[0-9a-f]{16}$")
def fetch(url):
    if not url.startswith(BASE) or not url.endswith(".csv"):raise ValueError("unapproved source")
    with urlopen(Request(url,headers={"User-Agent":"KennysSportsLabResearch/1.0"}),timeout=90) as r:
        raw=r.read(100_000_000)
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))),hashlib.sha256(raw).hexdigest()
def join(crosswalk,wide):
    cw={}
    for row in crosswalk:
        key=(row.get("fight_id") or row.get("ufcstats_fight_id") or "").strip().lower()
        if not HEX.fullmatch(key) or key in cw:raise ValueError("invalid or duplicate crosswalk fight id")
        cw[key]=row
    cols=set(wide[0]) if wide else set()
    candidates=[name for name in ("fight_id","ufcstats_fight_id","ufcstats_id") if name in cols]
    if not candidates:
        return {"status":"SCHEMA_BLOCKED","rows":len(wide),"columns":sorted(cols),
                "reason":"No native UFCStats fight ID column; refused name/date/row-order join",
                "matched":0,"unmatched":len(wide),"records":[]}
    id_col=candidates[0]
    matched=[];unmatched=[];seen=set()
    for row in wide:
        key=(row.get(id_col) or "").strip().lower()
        if not HEX.fullmatch(key):unmatched.append({"reason":"invalid_id","value":key});continue
        if key in seen:raise ValueError("duplicate wide fight ID: "+key)
        seen.add(key)
        if key not in cw:unmatched.append({"reason":"not_in_crosswalk","value":key});continue
        c=cw[key]
        matched.append({"ufcstats_fight_id":key,
          "ufcstats_event_id":c.get("ufc_event_id") or c.get("ufcstats_event_id"),
          "fighter_1_ufcstats_id":c.get("f1_id") or c.get("fighter_1_ufcstats_id"),
          "fighter_2_ufcstats_id":c.get("f2_id") or c.get("fighter_2_ufcstats_id"),
          "wide_record":row})
    return {"status":"JOINED" if matched else "NO_MATCHES","rows":len(wide),
            "matched":len(matched),"unmatched":len(unmatched),
            "match_rate":len(matched)/len(wide) if wide else 0,
            "unmatched_examples":unmatched[:20],
            "provenance":"RETROSPECTIVE_NOT_PIT_CERTIFIED","records":matched}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--crosswalk",default=BASE+"id_crosswalk_all.csv")
    p.add_argument("--wide",default=BASE+"ufc_all_fights_wide.csv")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.crosswalk.startswith("https://"):c,cs=fetch(a.crosswalk)
    else:
        raw=Path(a.crosswalk).read_bytes();cs=hashlib.sha256(raw).hexdigest()
        c=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if a.wide.startswith("https://"):w,ws=fetch(a.wide)
    else:
        raw=Path(a.wide).read_bytes();ws=hashlib.sha256(raw).hexdigest()
        w=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    result=join(c,w)
    result["source_hashes"]={"crosswalk":cs,"wide":ws}
    a.output.write_text(json.dumps(result,separators=(",",":"))+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="records"},indent=2))
    if result["status"]!="JOINED":raise SystemExit(2)
if __name__=="__main__":main()
