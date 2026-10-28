#!/usr/bin/env python3
"""Fail-closed NBA ML betting-readiness audit. Never infer ROI from current odds."""
import datetime as dt
import json
import pathlib

def audit(odds, model, now, schedule=None, archive=None):
    report={"status":"not_bet_eligible","checked_at":now.isoformat(),"checks":{}}
    checks=report["checks"]
    def fresh(obj,key):
        try:
            stamp=dt.datetime.fromisoformat(obj[key].replace("Z","+00:00"))
            return stamp.tzinfo is not None and 0 <= (now-stamp).total_seconds() <= 150*60
        except (ValueError,TypeError,KeyError,AttributeError):
            return False
    checks["odds_fresh"]=odds.get("status")=="ok" and fresh(odds,"fetched_at")
    checks["model_fresh_and_calibrated"]=model.get("status")=="validated" and model.get("calibration_passed") is True and fresh(model,"generated_at")
    schedule=schedule or {}
    archive=archive or {}
    checks["schedule_evidence_fresh"]=schedule.get("status")=="ok" and fresh(schedule,"fetched_at")
    checks["pregame_odds_archiving_active"]=archive.get("status")=="ok" and fresh(archive,"captured_at") and len(archive.get("rows",[]))>0
    checks["historical_pregame_odds_backtest"]=False
    checks["closing_line_value_verified"]=False
    checks["injury_lineup_rest_confirmed"]=False
    checks["executable_same_book_parlay_quote"]=False
    checks["correlation_stress_test_verified"]=False
    report["reason"]="Historical pregame odds, lineup availability, executable parlay prices and correlation validation are not connected; fail closed."
    return report

def main():
    def load(path):
        try:return json.loads(pathlib.Path(path).read_text())
        except (OSError,ValueError):return {}
    archive_root=pathlib.Path('data/nba_ml_odds_archive')
    archives=sorted(archive_root.glob('*/*.json')) if archive_root.exists() else []
    latest_archive=load(archives[-1]) if archives else {}
    report=audit(load("feed/basketball_nba.json"),load("feed/nba_ml_predictions.json"),dt.datetime.now(dt.timezone.utc),load("feed/nba_ml_schedule_evidence.json"),latest_archive)
    target=pathlib.Path("feed/nba_ml_betting_readiness.json")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+"\n")
    print("NBA ML betting readiness:",report["status"],report["checks"])
if __name__=="__main__":main()
