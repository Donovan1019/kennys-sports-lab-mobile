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

if __name__ == "__main__":
    audit()
