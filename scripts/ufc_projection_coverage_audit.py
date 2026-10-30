#!/usr/bin/env python3
"""Audit actual UFC projection coverage; fail on structural corruption, report gaps."""
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT / "feed" / name).read_text())

def norm(name):
    import unicodedata, re
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", s.lower())).strip()

def audit():
    event = load("ufc_research.json")
    stats = load("ufc_fighter_stats_mirror.json")
    elo = load("ufc_elo_projections.json")
    odds = load("mma_mixed_martial_arts.json")
    fights = event.get("fights", [])
    profiles = stats.get("fighters", [])
    by_name = {norm(f.get("name")): f for f in profiles if f.get("name")}
    elo_by_id = {str(x.get("fight_id")): x for x in elo.get("projections", [])}
    if len(by_name) != len([f for f in profiles if f.get("name")]):
        raise ValueError("Duplicate normalized fighter names")
    issues = Counter()
    rows = []
    for f in fights:
        names = [f.get("red"), f.get("blue")]
        if not all(names) or not f.get("id"):
            issues["invalid_bout"] += 1
            continue
        matched = [by_name.get(norm(n)) for n in names]
        for fighter in matched:
            if fighter is None:
                issues["fighter_profile_missing"] += 1
            elif fighter.get("career_round_totals", {}).get("round_rows", 0) <= 0:
                issues["fighter_round_history_missing"] += 1
        if f.get("scheduled_rounds") not in (3, 5):
            issues["scheduled_rounds_unverified"] += 1
        e = elo_by_id.get(str(f["id"]))
        if not e or e.get("red_elo") is None or e.get("blue_elo") is None:
            issues["two_sided_elo_missing"] += 1
        if not f.get("fighter_status_verified"):
            issues["fighter_status_unverified"] += 1
        rows.append({"fight_id": str(f["id"]), "red": names[0], "blue": names[1],
                     "matched_profiles": sum(x is not None for x in matched),
                     "rounds": f.get("scheduled_rounds"),
                     "two_sided_elo": bool(e and e.get("red_elo") is not None and e.get("blue_elo") is not None)})
    updated = odds.get("fetched_at")
    if not updated:
        issues["odds_timestamp_missing"] += 1
    else:
        stamp = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - stamp).total_seconds()
        if age > 6 * 3600 or age < -60:
            issues["odds_snapshot_stale"] += 1
    report = {"fight_count": len(fights), "fighter_profile_count": len(profiles),
              "odds_records": len(odds.get("odds", [])), "odds_fetched_at": updated,
              "issues": dict(issues), "fights": rows}
    print(json.dumps(report, indent=2))
    return report

def research_pipeline():
    """Single-pass, evidence-gated UFC research pipeline for every saved fight.

    Five stages: opponent evidence, uncertainty, verified-input count Monte Carlo,
    retrospective calibration, and executable-odds/EV gate. No missing data imputation
    is passed off as independently verified pre-fight information.
    """
    import math
    from ufc_bout_monte_carlo import simulate
    event, stats, elo = (load(n) for n in ("ufc_research.json", "ufc_fighter_stats_mirror.json", "ufc_elo_projections.json"))
    by_name = {norm(p["name"]): p for p in stats.get("fighters", []) if p.get("name")}
    by_id = {str(p.get("fight_id")): p for p in elo.get("projections", [])}
    rows = []
    for f in event.get("fights", []):
        red, blue = f.get("red"), f.get("blue")
        if not red or not blue: continue
        a, b = by_name.get(norm(red)), by_name.get(norm(blue))
        e = by_id.get(str(f.get("id")))
        ra = a.get("career_round_totals") if a else None
        rb = b.get("career_round_totals") if b else None
        n = min((ra or {}).get("round_rows") or 0, (rb or {}).get("round_rows") or 0)
        paired_elo = bool(e and e.get("red") == red and e.get("blue") == blue and
                          isinstance(e.get("red_elo"), (int,float)) and isinstance(e.get("blue_elo"), (int,float)))
        elo_diff = max(-.65, min(.65, (e["red_elo"]-e["blue_elo"])/500)) if paired_elo else 0
        def rate(t,k):
            return t.get(k)/t["round_rows"] if t and t.get("round_rows",0)>0 and isinstance(t.get(k),(int,float)) else None
        sr, sb = rate(ra,"sig_landed"),rate(rb,"sig_landed")
        tr, tb = rate(ra,"td_landed"),rate(rb,"td_landed")
        strike = max(-.5,min(.5,math.log((sr+3)/(sb+3))*.45)) if sr is not None and sb is not None else 0
        td = max(-.3,min(.3,math.log((tr+.5)/(tb+.5))*.18)) if tr is not None and tb is not None else 0
        strength = min(.8,n/(n+24)+(.2 if paired_elo else 0))
        probability = 1/(1+math.exp(-(elo_diff+strike+td)*strength))
        halfwidth = max(.12,min(.49,.49-.38*strength))
        sims = {}
        for name,t in ((red,ra),(blue,rb)):
            rounds=f.get("scheduled_rounds")
            if rounds not in (3,5) or not t or not t.get("round_rows") or any(not isinstance(t.get(k),(int,float)) for k in ("sig_landed","sig_attempted","td_landed","td_attempted")):
                sims[name]={"status":"UNAVAILABLE","reason":"Verified scheduled rounds or historical count rates missing"}
                if rounds not in (3,5) and t and t.get("round_rows"):
                    sims[name]["historical_per_round"]={k:round(t[k]/t["round_rows"],2) for k in ("sig_landed","sig_attempted","td_landed","td_attempted") if isinstance(t.get(k),(int,float))}
                    sims[name]["reason"]="Scheduled rounds UNVERIFIED; showing historical per-round rates only, not full-fight simulation"
                continue
            rates={key:t[field]/t["round_rows"] for key,field in (("sig_landed","sig_landed"),("sig_attempted","sig_attempted"),("takedowns_landed","td_landed"),("takedowns_attempted","td_attempted"))}
            result=simulate(rates,rounds,draws=1000,seed=2026)
            sims[name]={"status":"RESEARCH_ONLY","count_means":{k:round(v["mean"],2) for k,v in result["markets"].items()},"limitation":"Illustrative uncalibrated finish hazard; not sportsbook prop probabilities"}
        rows.append({"fight_id":str(f.get("id")),"red":red,"blue":blue,
                     "opponent_adjustment":{"elo_available":paired_elo,"verified_strength_of_schedule":False},
                     "sparse_data_probability":{"red":round(probability,4),"blue":round(1-probability,4),
                                                "red_uncertainty_interval":[round(max(.01,probability-halfwidth),4),round(min(.99,probability+halfwidth),4)],
                                                "status":"NEUTRAL_PRIOR" if strength==0 else "UNCALIBRATED_RESEARCH"},
                     "count_simulation":sims,
                     "calibration":{"status":"UNVERIFIED","point_in_time_validated":False},
                     "betting":{"status":"NOT_ELIGIBLE","model_ev":None,"reason":"No calibrated independent live probability and verified executable price"}})
    return {"schema":1,"sport":"UFC","research_only":True,"bet_eligible":False,"fights":rows,
            "limitations":["Pre-UFC career and opponent-adjusted style histories not verified",
                           "No independent point-in-time calibration or validated EV",
                           "Count Monte Carlo uses illustrative finish hazard only"]}


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--pipeline-output",type=Path)
    args=parser.parse_args()
    if args.pipeline_output:
        report=research_pipeline()
        args.pipeline_output.parent.mkdir(parents=True,exist_ok=True)
        args.pipeline_output.write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps({"fights":len(report["fights"]),"bet_eligible":False}))
    else:
        audit()

