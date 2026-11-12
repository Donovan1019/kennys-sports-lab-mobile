# NFL WR Opportunity: verified source expansion (2026)

## Source priority and constraints
1. **nflverse weekly player stats** — existing targets, receptions, receiving yards, touchdowns. Published in `stats_player` release. Do not treat the sum of observed targets as independently audited full-team targets.
2. **nflverse PFR snap counts** — weekly offensive snaps; join via mapped player IDs, team, season, week. Source: https://nflreadr.nflverse.com/reference/load_snap_counts.html . Verify PFR name/ID mapping before ingestion.
3. **FTN charting via nflverse** — read_thrown on targeted plays can identify first-read targets when value is 1 or DES; must join charted pass plays to nflverse PBP and verify coverage at the *game* level before counting. Attribution: FTN Data via nflverse, CC BY-SA 4.0. Source: https://nflreadr.nflverse.com/reference/load_ftn_charting.html .
4. **nflverse play-by-play** — pass location, yardline and end-zone targets may be derivable from explicitly targeted pass plays with verified field-position conventions. End-zone targets require target location, **not** merely line of scrimmage inside the 20. Do not equate red-zone targets to end-zone targets.
5. **Routes run** — no confirmed free, current-season all-route player-game source with automated reuse rights. Fantasy Life utilization game log provides route usage percentages (https://www.fantasylife.com/nfl/utilization-report/game-log), but percentage is **not** an exact route count. Confirm permission/API/export and denominator before importing. Do not synthesize counts from offensive snaps or passing downs.
6. **FTN participation** — not a substitute for current-season routes. nflverse notes that participation data for recent seasons is released after the postseason, not in-season: https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html .

## Enrichment contract
Use `scripts/enrich_nfl_wr_opportunity.py` only with a verified licensed supplemental CSV. Required exact keys: season,week,team,player_id. Numeric optional fields: offensive_snaps,routes_run,team_dropbacks,first_read_targets,team_first_read_targets,end_zone_targets,team_end_zone_targets. Reject duplicates, invalid metrics, and conflicts. Record source attribution on each enriched metric. No joins by player name alone.

## Validation before publishing
- Check team-week game completeness and season/week uniqueness.
- Reject missing/ambiguous player ID mappings; do not coerce unknown players to a similar name.
- For each metric report numerator/denominator coverage by week and team.
- First-read and end-zone team denominators must come from the **same charted games** as player numerators.
- Preserve null for unverified metrics; UI shows unavailable instead of zero.
- Confirm redistribution rights before automated extraction from commercial dashboards.
