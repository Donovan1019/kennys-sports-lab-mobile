#!/usr/bin/env python3
"""Read-only UFC simulator input coverage audit. Never certifies betting eligibility."""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def normalize(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", value.lower())).strip()

def audit(card, mirror, simulations):
    if not isinstance(card.get("fights"), list) or not isinstance(mirror.get("fighters"), list):
        raise ValueError("Invalid fighter/card schema")
    profiles = {normalize(f.get("name")): f for f in mirror["fighters"] if f.get("name")}
    blocked = {str(b.get("fight_id")): b.get("reason") for b in simulations.get("blocked", [])}
    rows = []
    for fight in card["fights"]:
        sides = {}
        for corner in ("red", "blue"):
            name = fight.get(corner)
            profile = profiles.get(normalize(name))
            sides[corner] = {
                "name": name,
                "mirror_status": profile.get("status") if profile else "ABSENT",
                "historical_round_rows": (profile.get("career_round_totals") or {}).get("round_rows") if profile else None,
                "stats_asof_verified": profile.get("stats_asof_verified") is True if profile else False,
                "fighter_status_verified": profile.get("fighter_status_verified") is True if profile else False,
            }
        rows.append({
            "fight_id": str(fight.get("id")),
            "fighters": sides,
            "scheduled_rounds_verified": fight.get("scheduled_rounds") in (3, 5),
            "simulator_blocker": blocked.get(str(fight.get("id"))),
            "bet_eligible": False,
        })
    return {
        "sport": "UFC",
        "status": "RESEARCH_ONLY",
        "bet_eligible": False,
        "card_fights": len(rows),
        "blocked_fights": sum(bool(row["simulator_blocker"]) for row in rows),
        "matched_historical_sides": sum(side["mirror_status"] == "MATCHED_HISTORICAL_STATS" for row in rows for side in row["fighters"].values()),
        "ambiguous_historical_sides": sum(side["mirror_status"] == "INSUFFICIENT_OR_AMBIGUOUS" for row in rows for side in row["fighters"].values()),
        "absent_historical_sides": sum(side["mirror_status"] == "ABSENT" for row in rows for side in row["fighters"].values()),
        "verified_scheduled_round_fights": sum(row["scheduled_rounds_verified"] for row in rows),
        "fights": rows,
        "limitations": ["Historical profile coverage does not prove simulator feature-join correctness", "No independent calibrated moneyline model or point-in-time certification"],
    }

def main():
    card = json.loads((ROOT / "feed/ufc_research.json").read_text())
    mirror = json.loads((ROOT / "feed/ufc_fighter_stats_mirror.json").read_text())
    simulations = json.loads((ROOT / "feed/ufc_simulations.json").read_text())
    print(json.dumps(audit(card, mirror, simulations), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
