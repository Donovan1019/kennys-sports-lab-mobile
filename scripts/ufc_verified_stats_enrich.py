#!/usr/bin/env python3
"""Fail-closed adapter for authorized, manually verified UFC fighter-stat records."""
import argparse
import json
import math
from pathlib import Path

METHODS = ("ko_rate", "submission_rate", "decision_rate")

def verified_stats(record):
    if not isinstance(record, dict) or record.get("source_permission_verified") is not True or record.get("stats_verified") is not True:
        return None
    if not record.get("source") or not record.get("source_record_id") or not record.get("verified_at"):
        return None
    sample = record.get("sample_size")
    if type(sample) is not int or sample < 10:
        return None
    values = [record.get(key) for key in METHODS]
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in values):
        return None
    if abs(sum(values) - 1) > 0.01:
        return None
    return {**dict(zip(METHODS, values)), "sample_size": sample}

def enrich(card, source):
    records = source.get("fighters", [])
    if not isinstance(records, list) or source.get("source_permission_verified") is not True:
        raise ValueError("Stats feed permission not verified")
    by_name = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        name = record.get("name")
        if not isinstance(name, str) or not name.strip() or name in by_name:
            raise ValueError("Missing or duplicate fighter identity")
        by_name[name] = record
    enriched, blocked = [], []
    for fight in card.get("fights", []):
        f = dict(fight)
        reasons = []
        for side in ("red", "blue"):
            stats = verified_stats(by_name.get(f.get(side)))
            if stats is None:
                reasons.append("Missing verified, licensed stats: " + side)
            else:
                f[side + "_stats"] = stats
        if f.get("scheduled_rounds") not in (3, 5):
            reasons.append("Unverified scheduled rounds")
        if f.get("fighter_status_verified") is not True:
            reasons.append("Fighter status not verified")
        f["stats_verified"] = not any("stats" in reason for reason in reasons)
        f["bet_eligible"] = False
        if reasons:
            blocked.append({"fight_id": f.get("id"), "reasons": reasons})
        enriched.append(f)
    return {"schema": 1, "sport": "UFC", "fights": enriched, "blocked": blocked, "bet_eligible": False, "research_only": True}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--card", default="feed/ufc_research.json")
    parser.add_argument("--stats", required=True, help="Authorized verified stats JSON")
    parser.add_argument("--output", default="feed/ufc_enriched_research.json")
    args = parser.parse_args()
    result = enrich(json.loads(Path(args.card).read_text()), json.loads(Path(args.stats).read_text()))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\\n")
    print("Enriched UFC fights:", len(result["fights"]), "blocked:", len(result["blocked"]))

if __name__ == "__main__":
    main()
