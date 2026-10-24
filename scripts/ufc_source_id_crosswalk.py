#!/usr/bin/env python3
"""UFCStats <-> odds/scorecards fight-ID crosswalk, with conservative quality gates.

Source: nlbair/ufc-data CC BY 4.0. Crosswalk keys are original UFCStats IDs.
Never join independent sources by row order or fighter name alone.
"""
import argparse,csv,hashlib,io,json,re
from pathlib import Path
from urllib.request import Request,urlopen

BASE="https://raw.githubusercontent.com/nlbair/ufc-data/main/data/"
HEX=re.compile(r"^[a-f0-9]{16}$")
def download(source):
    if source.startswith("https://"):
        if not source.startswith(BASE):raise ValueError("unapproved source")
        with urlopen(Request(source,headers={"User-Agent":"KennysSportsLabResearch/1.0"}),timeout=60) as r:
            raw=r.read(60_000_000)
    else:raw=Path(source).read_bytes()
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))),hashlib.sha256(raw).hexdigest()
def confidence(row):
    if not row.get("mmad_decision_id"):return "UNLINKED"
    try:
        name=float(row["mmad_name_sim"])
        gap=abs(float(row["mmad_day_gap"]))
        cards=float(row["mmad_total_agree"])
    except (ValueError,TypeError,KeyError):return "UNVERIFIED"
    return "HIGH" if name>=.9 and gap<=1 and cards>=2 else "REVIEW"
def build(rows,source_sha):
    seen=set();fights=[];issues=[]
    for i,r in enumerate(rows):
        fid=(r.get("fight_id") or "").strip().lower()
        f1=(r.get("f1_id") or "").strip().lower()
        f2=(r.get("f2_id") or "").strip().lower()
        event=(r.get("ufc_event_id") or "").strip().lower()
        if not all(HEX.fullmatch(v) for v in (fid,f1,f2,event)) or f1==f2:
            issues.append({"row":i,"reason":"invalid UFCStats identifiers"});continue
        if fid in seen:issues.append({"row":i,"reason":"duplicate fight_id"});continue
        seen.add(fid)
        fights.append({"ufcstats_fight_id":fid,"ufcstats_event_id":event,
            "fighter_1_ufcstats_id":f1,"fighter_2_ufcstats_id":f2,
            "mma_decisions_id":(r.get("mmad_decision_id") or "").strip() or None,
            "mma_decisions_match_quality":confidence(r),
            "bestfightodds_profile_url":(r.get("bfo_profile_url") or "").strip() or None,
            "bfo_owner_id":(r.get("bfo_owner_id") or "").strip() or None,
            "bfo_owner_similarity":(r.get("bfo_owner_sim") or "").strip() or None,
            "bfo_opponent_similarity":(r.get("bfo_opponent_sim") or "").strip() or None})
    if issues:raise ValueError("invalid crosswalk rows: "+json.dumps(issues[:8]))
    if not fights:raise ValueError("empty crosswalk")
    return {"source":BASE+"id_crosswalk_all.csv","source_sha256":source_sha,
      "provenance":"RETROSPECTIVE_SOURCE_ID_CROSSWALK_NOT_PIT_CERTIFIED",
      "bet_eligible":False,"count":len(fights),
      "mma_decisions_high_confidence":sum(x["mma_decisions_match_quality"]=="HIGH" for x in fights),
      "fights":fights}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default=BASE+"id_crosswalk_all.csv")
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    rows,sha=download(args.source)
    out=build(rows,sha)
    args.output.write_text(json.dumps(out,separators=(",",":"))+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="fights"},indent=2))
if __name__=="__main__":main()
