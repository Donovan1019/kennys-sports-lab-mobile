"""Reconcile UFC joined research with the current ESPN card; never certify betting data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "feed"


def reconcile(card, joined, mirror, elo):
    by_name = {f["name"].casefold(): f for f in mirror.get("fighters", []) if f.get("name")}
    by_elo = {str(f["fight_id"]): f for f in elo.get("projections", []) if f.get("fight_id")}
    old = {str(f["fight_id"]): f for f in joined.get("fights", [])}
    fights = []
    for card_fight in card.get("fights", []):
        eid = str(card_fight["id"])
        names = {side: card_fight[side] for side in ("red", "blue")}
        existing = old.get(eid, {})
        fighters = {}
        for side, name in names.items():
            source = by_name.get(name.casefold(), {})
            previous = existing.get("fighters", {}).get(side, {})
            hist = source.get("career_round_totals")
            fighters[side] = {
                "name": name, "mirror_status": source.get("status", "UNAVAILABLE"),
                "source_profile": source.get("source_profile"),
                "historical_career_round_totals": hist,
                "stats_asof_verified": False, "fighter_status_verified": False,
                "unified_count_research": previous.get("unified_count_research")
                    if previous.get("name") == name and previous.get("unified_count_research")
                    else {"status": "UNAVAILABLE", "reason": "No verified pre-fight count simulation",
                          "historical_per_round": None},
            }
        projection = by_elo.get(eid, {})
        ratings = (projection.get("red_elo"), projection.get("blue_elo"))
        valid_elo = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in ratings)
        rounds = card_fight.get("scheduled_rounds")
        fights.append({
            "fight_id": eid, **names, "fighters": fighters,
            "elo": {"red": ratings[0], "blue": ratings[1]} if valid_elo else None,
            "sparse_data_probability": None,
            "verified_scheduled_rounds": rounds if rounds in (3, 5) else None,
            "legacy_simulation_blocker": "Independent simulation not verified",
            "calibration": {"status": "UNVERIFIED", "point_in_time_validated": False,
                            "evaluated_fights": 0, "brier": None, "log_loss": None},
            "model_ev": None, "bet_eligible": False,
        })
    joined["fights"] = fights
    joined["research_only"] = True
    joined["bet_eligible"] = False
    joined["coverage"] = {
        "fights": len(fights),
        "fighter_sides_with_historical_stats": sum(bool(side["historical_career_round_totals"])
            for f in fights for side in f["fighters"].values()),
        "paired_historical_matchups": sum(all(bool(s["historical_career_round_totals"])
            for s in f["fighters"].values()) for f in fights),
        "paired_elo_matchups": sum(f["elo"] is not None for f in fights),
        "verified_scheduled_round_fights": sum(f["verified_scheduled_rounds"] in (3, 5) for f in fights),
        "legacy_blocked_fights": len(fights),
    }
    return joined


def main():
    def load(name):
        return json.loads((ROOT / name).read_text())
    updated = reconcile(load("ufc_research.json"), load("ufc_joined_stats.json"),
                        load("ufc_fighter_stats_mirror.json"), load("ufc_elo_projections.json"))
    (ROOT / "ufc_joined_stats.json").write_text(json.dumps(updated, indent=2) + "\n")


if __name__ == "__main__":
    main()
