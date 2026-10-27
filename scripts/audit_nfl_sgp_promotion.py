#!/usr/bin/env python3
"""Fail-closed NFL SGP promotion evidence audit."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(p): return json.loads((ROOT / p).read_text(encoding="utf-8"))
score=read("feed/americanfootball_nfl_correlation_backtest.json")
walk=read("feed/nfl_sgp_walkforward_accuracy.json")
readiness=read("feed/player_recommendation_readiness.json")
stats=read("feed/nfl_player_stats.json")
game_logs=[g for p in stats.get("players",[]) for g in p.get("games",[])]
identified_logs=sum(bool(g.get("game_id") or g.get("event_id")) for g in game_logs)
delta=float(score["correlated"]["brier"])-float(score["independent"]["brier"])
checks={
"score_correlation_improves_brier":delta<0 and score.get("promotion_approved") is True,
"player_prop_same_game_joint_holdout":False,
"player_game_identity_coverage":bool(game_logs) and identified_logs==len(game_logs),
"player_prop_joint_vs_independent_brier":False,
"forward_calibrated_live_player_props":False,
"independent_current_roster_and_injury_validation":False,
"verified_actual_sgp_bookmaker_quote":False,
"same_game_sgp_expected_value_validated":False}
report={"status":"BLOCKED","betting_eligible":False,"checks":checks,
"score_backtest_sample_size":score.get("sample_size"),
"player_week_log_count":len(game_logs),
"player_logs_with_game_identity":identified_logs,
"score_correlated_minus_independent_brier":round(delta,8),
"score_correlation_promoted":score.get("promotion_approved") is True,
"walkforward_status":walk.get("status"),
"readiness_source_present":isinstance(readiness,dict),
"limitations":"Game/event IDs must be present for reliable same-game joins. Score correlation is not same-game player-prop validation. No independently verified actual SGP quote or forward joint holdout."}
print(json.dumps(report,indent=2,sort_keys=True))
