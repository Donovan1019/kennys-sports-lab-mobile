#!/usr/bin/env python3
"""Audit actual archived pregame NFL coverage, without inventing backtest results."""
import json
from pathlib import Path
from scripts.join_nfl_pregame_results import join

ROOT = Path(__file__).resolve().parents[1]

def audit(root=ROOT):
    completed = json.loads((root / "feed/nfl_completed_games.json").read_text())
    archive_files = list((root / "archive/nfl_moneyline/inputs").glob("*.json"))
    result = join(root)
    return {
        "completed_results": len(completed.get("games", [])),
        "pregame_input_archive_files": len(archive_files),
        "matched_pregame_snapshots": result["joined_snapshots"],
        "unique_completed_games_with_pregame_inputs": result["unique_games"],
        "historical_predictions_verified": False,
        "calibrated_accuracy_available": False,
        "status": "COVERAGE_AVAILABLE" if result["unique_games"] else "NO_MATCHED_PREGAME_ARCHIVES"
    }

if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
