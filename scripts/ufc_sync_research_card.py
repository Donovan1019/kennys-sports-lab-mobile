"""Align current UFC research and mirror to the authoritative card, fail closed."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"feed"
def sync(card, unified, mirror):
    old={(str(f.get("fight_id")),f.get("red"),f.get("blue")):f for f in unified["fights"]}
    rows=[]
    for f in card["fights"]:
        k=(str(f["id"]),f["red"],f["blue"])
        rows.append(old.get(k,{"fight_id":k[0],"red":k[1],"blue":k[2],"sparse_data_probability":None,"count_simulation":{},"calibration":{"status":"UNVERIFIED"},"betting":{"status":"NOT_ELIGIBLE","model_ev":None,"reason":"Current fight research unavailable"}}))
    unified["fights"]=rows
    unified["coverage"]={"fights":len(rows),"matched_existing_research":sum((r["fight_id"],r["red"],r["blue"]) in old for r in rows)}
    unified["bet_eligible"]=False
    names=sorted({f[s] for f in card["fights"] for s in ("red","blue")})
    profiles={p["name"]:p for p in mirror["fighters"]}
    mirror["fighters"]=[profiles.get(n,{"name":n,"status":"INSUFFICIENT_OR_AMBIGUOUS","career_round_totals":None,"stats_asof_verified":False,"fighter_status_verified":False,"bet_eligible":False}) for n in names]
    return unified,mirror
def main():
    def read(n):return json.loads((ROOT/n).read_text())
    names=["ufc_unified_research.json","ufc_fighter_stats_mirror.json"]
    for n,d in zip(names,sync(read("ufc_research.json"),*(read(n) for n in names))):
        (ROOT/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
if __name__=="__main__":main()
