#!/usr/bin/env python3
"""Offline NFL data readiness audit; research-only, no inferred player identity."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

def audit(stats, usage, injuries, cross):
    players=stats.get("players",[])
    profiles=usage.get("profiles",[])
    candidates=cross.get("candidates",[])
    player_ids=[str(p.get("id")) for p in players if p.get("id")]
    profile_ids=[str(p.get("nflverse_player_id")) for p in profiles if p.get("nflverse_player_id")]
    espn_ids=[str(r.get("espn_athlete_id")) for r in injuries.get("injuries",[]) if r.get("espn_athlete_id")]
    fresh=int(cross.get("name_team_candidates",0))
    stale=int(cross.get("historical_name_team_candidates",0))
    unmatched=int(cross.get("no_match",0))
    ambiguous=int(cross.get("ambiguous",0))
    if len(profile_ids)!=len(set(profile_ids)):
        raise ValueError("Duplicate nflverse profile IDs; refuse identity readiness")
    if fresh+stale+unmatched+ambiguous!=len(profiles):
        raise ValueError("Inconsistent injury crosscheck counts")
    return {
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "status":"RESEARCH_ONLY","betting_eligible":False,
        "identity_crosswalk_verified":False,"game_day_availability_verified":False,
        "players_in_stats":len(players),"unique_nflverse_player_ids":len(set(player_ids)),
        "usage_profiles":len(profiles),"usage_profiles_with_nflverse_id":len(profile_ids),
        "injury_observations":len(injuries.get("injuries",[])),
        "injury_observations_with_espn_id":len(espn_ids),
        "unique_espn_ids_observed":len(set(espn_ids)),
        "fresh_name_team_candidates":fresh,"historical_stale_matches":stale,
        "unmatched_profiles":unmatched,"ambiguous_profiles":ambiguous,
        "source_feed_fresh":bool(cross.get("injury_feed_fresh")),
        "blockers":["NO_VERIFIED_CROSS_PROVIDER_IDENTITY","NO_CONFIRMED_GAME_DAY_AVAILABILITY","NO_VALIDATED_INJURY_ADJUSTMENT"],
        "notes":"Source-native IDs are not an independently verified crosswalk; never promote name/team matches to betting eligibility."
    }

def main():
    root=Path(__file__).resolve().parent.parent/"feed"
    def load(name):return json.loads((root/name).read_text())
    report=audit(load("nfl_player_stats.json"),load("nfl_usage_research.json"),load("nfl_injury_observations.json"),load("nfl_injury_usage_crosscheck.json"))
    (root/"nfl_identity_coverage_audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print("NFL identity coverage",json.dumps({k:v for k,v in report.items() if k not in ("notes","blockers")}))
if __name__=="__main__":main()
