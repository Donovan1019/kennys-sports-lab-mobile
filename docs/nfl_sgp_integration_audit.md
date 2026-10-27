# NFL SGP existing-engine integration audit — 2026-10-27

## Decision
Reuse existing models and backtests. Do not build a duplicate SGP simulator or promote unverified odds quotes to picks.

## Verified components on main
| Component | File | Current role | Gate |
| --- | --- | --- | --- |
| Exact two-way archived forecast matching | `nfl_sgp_stack_finder.js` and `feed/nfl_prop_forecast_ledger.json` | Displays historical Over/Under lean only when event, player, market, line, book, and two-sided quoted prices match | Research only; 538 archived forecasts |
| SGP joint historical bootstrap | `nfl_sgp_joint_bootstrap.js` | Paired calendar-week player stat draws; NOT guaranteed same-game/opponent dependence | Experimental; cannot be interpreted as calibrated SGP probability |
| NFL player-prop walk-forward | `scripts/audit_nfl_sgp_walkforward.py` and `feed/nfl_sgp_walkforward_accuracy.json` | 8,912 historical evaluations; synthetic thresholds, not sportsbook lines | Research only; live betting blocked |
| NFL score correlation backtest | `feed/americanfootball_nfl_correlation_backtest.json` | 367 historical score outcomes, 10,000 trials per game | `promotion_approved: false`; NOT player-prop correlation validation |
| Recommendation readiness | `feed/player_recommendation_readiness.json` | Cross-sport eligibility and source-integrity audit | NFL fully verified player recommendations: 0; no independent current roster match |
| Forecast archival/export | `scripts/export_nfl_prop_forecasts.cjs` and `scripts/archive_nfl_prop_forecasts.cjs` | Pregame exact-line two-way records | `research_only: true`, `betting_eligible: false` |
| Four-core Kenny's SGP audit | `kennys_sgp.js` | QB, WR, RB, team total availability | Availability checklist, not an SGP recommendation |

## Frozen forward-holdout gates
- Passing yards: FAILED_DUAL_METRIC_GATE.
- Receiving yards: FAILED_DUAL_METRIC_GATE.
- Receptions: FAILED_DUAL_METRIC_GATE.
- Rushing yards: BOTH_METRICS_IMPROVED, but `eligible_for_live_use: false`.
- None of these historical tests validate sportsbook-line EV, injuries, current team assignment, or an official same-game parlay price.

## Nonduplicative integration plan
1. **Identity and timestamp gate:** use archived forecast IDs to match event, player, market, numeric line, side, bookmaker, quote timestamp, and kickoff; reject stale, conflicting, or missing two-way quotes. Never infer a model pick from an offered Over.
2. **Eligibility gate:** consume recommendation-readiness output and market-specific calibration status. Do not promote any player until current team, role, injury, source, and genuinely independent forward outcomes are verified.
3. **Joint-model gate:** reuse the existing joint-bootstrap interface as *historical diagnostics only*. Require a separately validated same-game joint forecast and stress tests before quoting SGP win probability.
4. **Price and EV gate:** only compute SGP EV from a verified *actual SGP sportsbook quote*, not a multiplication of individual-leg prices; report no EV if absent.
5. **UI gate:** distinguish `MARKET AVAILABLE`, `HISTORICAL MODEL LEAN — RESEARCH ONLY`, `BLOCKED`, and `BET ELIGIBLE`. The last state must be unreachable until all upstream gates pass.
6. **Regression test:** ensure a quoted Over 6.5 with model Over probability 0.40 cannot be displayed as an Over recommendation; ensure changing event/line/book/quote prices prevents a historical match; ensure under-side support does not silently become a betting recommendation.

## Acceptance
Do not remove existing sports, markets, Monte Carlo, Diamond Plays, or four-core SGP modules. A successful UI integration alone is not a betting-readiness validation. Keep fail-closed defaults and report missing inputs explicitly.
