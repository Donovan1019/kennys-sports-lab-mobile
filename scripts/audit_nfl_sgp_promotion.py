#!/usr/bin/env python3
"""Fail-closed NFL SGP promotion evidence audit."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(p): return json.loads((ROOT / p).read_text(encoding="utf-8"))
score=read("feed/americanfootball_nfl_correlation_backtest.json")
walk=read("feed/nfl_sgp_walkforward_accuracy.json")
readiness=read("feed/player_recommendation_readiness.json")
delta=float(score["correlated"]["brier"])-float(score["independent"]["brier"])
checks={
"score_correlation_improves_brier":delta<0 and score.get("promotion_approved") is True,
"player_prop_same_game_joint_holdout":False,
"player_prop_joint_vs_independent_brier":False,
"forward_calibrated_live_player_props":False,
"independent_current_roster_and_injury_validation":False,
"verified_actual_sgp_bookmaker_quote":False,
"same_game_sgp_expected_value_validated":False}
report={"status":"BLOCKED","betting_eligible":False,"checks":checks,
"score_backtest_sample_size":score.get("sample_size"),
"score_correlated_minus_independent_brier":round(delta,8),
"score_correlation_promoted":score.get("promotion_approved") is True,
"walkforward_status":walk.get("status"),
"readiness_source_present":isinstance(readiness,dict),
"limitations":"Score correlation is not same-game player-prop validation. No independently verified actual SGP quote or forward joint holdout."}
print(json.dumps(report,indent=2,sort_keys=True))
