#!/usr/bin/env python3
"""Join existing UFC card, fighter mirror, Elo, and unified research into one evidence-gated feed."""
import json
from pathlib import Path
from scripts.ufc_simulator_input_audit import normalize

ROOT = Path(__file__).resolve().parents[1]
def join(card, mirror, elo, unified, legacy):
    fights = card.get("fights", [])
    profiles = {normalize(p["name"]): p for p in mirror.get("fighters", []) if p.get("name")}
    ratings = {str(p.get("fight_id")): p for p in elo.get("projections", [])}
    research = {str(p.get("fight_id")): p for p in unified.get("fights", [])}
    blocked = {str(p.get("fight_id")): p.get("reason") for p in legacy.get("blocked", [])}
    rows = []
    for fight in fights:
        fid = str(fight.get("id"))
        prior = research.get(fid, {})
        corners = {}
        for corner in ("red", "blue"):
            name = fight.get(corner)
            profile = profiles.get(normalize(name))
            totals = (profile or {}).get("career_round_totals") or {}
            valid = bool(profile and profile.get("status") == "MATCHED_HISTORICAL_STATS" and totals.get("round_rows", 0) > 0)
            corners[corner] = {
                "name": name,
                "mirror_status": profile.get("status") if profile else "ABSENT",
                "source_profile": profile.get("source_profile") if profile else None,
                "historical_career_round_totals": totals if valid else None,
                "stats_asof_verified": profile.get("stats_asof_verified") is True if profile else False,
                "fighter_status_verified": profile.get("fighter_status_verified") is True if profile else False,
                "unified_count_research": (prior.get("count_simulation") or {}).get(name),
            }
        rating = ratings.get(fid)
        paired_elo = bool(rating and rating.get("red") == fight.get("red") and rating.get("blue") == fight.get("blue")
                          and isinstance(rating.get("red_elo"), (int, float)) and isinstance(rating.get("blue_elo"), (int, float)))
        rows.append({
            "fight_id": fid, "red": fight.get("red"), "blue": fight.get("blue"),
            "fighters": corners,
            "elo": {"red": rating["red_elo"], "blue": rating["blue_elo"]} if paired_elo else None,
            "sparse_data_probability": prior.get("sparse_data_probability"),
            "verified_scheduled_rounds": fight.get("scheduled_rounds") if fight.get("scheduled_rounds") in (3, 5) else None,
            "legacy_simulation_blocker": blocked.get(fid),
            "calibration": prior.get("calibration", {"status": "UNVERIFIED"}),
            "model_ev": None, "bet_eligible": False,
        })
    return {
        "schema": 1, "sport": "UFC", "research_only": True, "bet_eligible": False,
        "coverage": {
            "fights": len(rows),
            "fighter_sides_with_historical_stats": sum(bool(s["historical_career_round_totals"]) for r in rows for s in r["fighters"].values()),
            "paired_historical_matchups": sum(all(s["historical_career_round_totals"] for s in r["fighters"].values()) for r in rows),
            "paired_elo_matchups": sum(r["elo"] is not None for r in rows),
            "verified_scheduled_round_fights": sum(r["verified_scheduled_rounds"] is not None for r in rows),
            "legacy_blocked_fights": sum(r["legacy_simulation_blocker"] is not None for r in rows),
        },
        "fights": rows,
        "limitations": ["Historical career totals are not point-in-time certified", "Elo and sparse-data probabilities are research-only", "No calibrated moneyline EV or executable betting recommendations"],
    }

def main():
    def load(name): return json.loads((ROOT / "feed" / name).read_text())
    result = join(load("ufc_research.json"), load("ufc_fighter_stats_mirror.json"), load("ufc_elo_projections.json"), load("ufc_unified_research.json"), load("ufc_simulations.json"))
    dest = ROOT / "feed/ufc_joined_stats.json"
    dest.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result["coverage"], indent=2))
if __name__ == "__main__": main()
