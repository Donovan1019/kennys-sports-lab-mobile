import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
r=subprocess.run([sys.executable,str(root/"scripts/audit_nfl_sgp_promotion.py")],cwd=root,capture_output=True,text=True,check=True)
d=json.loads(r.stdout)
assert d["status"]=="BLOCKED" and d["betting_eligible"] is False
assert d["checks"]["player_prop_same_game_joint_holdout"] is False
assert d["player_logs_with_game_identity"] <= d["player_week_log_count"]
assert d["checks"]["player_game_identity_coverage"] == (d["player_week_log_count"] > 0 and d["player_logs_with_game_identity"] == d["player_week_log_count"])
assert d["checks"]["verified_actual_sgp_bookmaker_quote"] is False
assert d["checks"]["same_game_sgp_expected_value_validated"] is False
print("SGP evidence gate passed")
