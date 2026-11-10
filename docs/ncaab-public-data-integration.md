# NCAA men's basketball: no-key data-source integration registry

Priority | Source | Data | Integration rule
--- | --- | --- | ---
1 | [SportsDataverse hoopR-mbb-data](https://github.com/sportsdataverse/hoopR-mbb-data) | ESPN-derived historical team/player boxes, schedules, rosters, play-by-play, shots, ratings, player value, crosswalks | Audit public GitHub release metadata; ingest only explicitly validated release assets with verified schema and event IDs
1 | [ESPN men's college basketball](https://www.espn.com/mens-college-basketball/) | Scoreboards, box scores, team and player stats | Existing bounded historical fetch; no fabricated rows
2 | [NCAA statistics](https://stats.ncaa.org/) | Official team/player statistics, game results | Verify access policy; cross-check identities and score totals, avoid uncontrolled scraping
2 | [Bart Torvik](https://barttorvik.com/) | Opponent-adjusted efficiency, pace, four factors | Research/verification source only until permitted automated access and date-safe snapshots are confirmed
2 | [CollegeBasketballData](https://collegebasketballdata.com/) | Historical CSV exports, lineups, shots, ratings, odds history | Use permitted free CSV export; REST API requires a key; preserve source attribution
3 | [College Basketball Reference](https://www.sports-reference.com/cbb/) | Historical team/player summaries | Manual cross-check only until automation terms and access are verified

## Acceptance gates before model consumption
1. Verify license/terms, download size, format, season, and source timestamp; never bypass blocks.
2. Validate unique event and team/player IDs with crosswalks, completed-game status, two teams, score and possession fields, and season boundaries.
3. Store raw immutable provenance, deduplicate by canonical game ID, compare ESPN/NCAA score discrepancies, and quarantine conflicts.
4. Generate features only from data known **before** the predicted game's start; prevent postgame leakage, transfers and roster churn from contaminating priors.
5. Walk-forward test previous seasons separately from the current season, calibrate probability distributions, and report Brier/log loss and coverage.
6. Display a betting recommendation only with verified fresh odds, matched market, calibrated probabilities, positive EV after uncertainty, and settlement checks.

**Current state:** The automated SportsDataverse release audit is metadata-only. This registry does not assert that new statistics are ingested or that picks are ready.
