# Verified NFL WR charting exports

The refresh workflow imports every CSV in this folder. Files are **not** generated automatically from Fantasy Life or FTN; a licensed, verified source export must be supplied first.

Required CSV keys: `season,week,team,player_id` (GSIS ID matching the base feed). Optional columns: `routes_run,team_dropbacks,first_read_targets,team_first_read_targets,end_zone_targets,team_end_zone_targets,offensive_snaps`.

Keep the same team-week denominator on all player rows; do not derive end-zone targets from red-zone targets or route counts from snaps. The enrichment script rejects duplicate and conflicting rows, but a passing script does not prove the external provider's completeness or permission to redistribute.

**Current source status**: nflverse weekly targets available in the base pipeline; PFR snap counts attempted automatically with exact-ID gating; FTN play charting and Fantasy Life routes/end-zone counts require source-specific normalized exports and coverage verification. Do not publish fabricated rows.
