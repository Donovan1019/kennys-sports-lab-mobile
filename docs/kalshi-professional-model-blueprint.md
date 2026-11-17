# Kenny's Kalshi — Independent Professional Modeling Blueprint

Status: design contract; NOT evidence that advanced integrations are implemented.

## Reference principles (independently reimplement, do not copy proprietary code)
- RotoGrinders: sport-specific projections, matchup/news adjustments, pick grade and model win percentage. https://rotogrinders.com/kalshi/predictions
- Unabated: blended projections, scenario distributions and Monte Carlo alternate-line fair pricing. https://unabated.com/tools/core/props-simulator
- Troxler: compare executable Kalshi asks with de-vigged sportsbook consensus; account for spread and depth. https://troxler.io/
- PlayDelta: pregame timestamps, exact market matching, evidence and calibration scorecard. https://play-delta.com/kalshi/
- Kalshi calibration research: evaluate reliability by volume and time-to-event. https://kalshi.com/research/publications/calibration

## Required pipeline
1. Normalize fixtures, aliases, team/opponent/date, and settlement rules. Reject ambiguous or incompatible contracts.
2. Load independently generated sport-specific projections with versioned feature provenance: injuries, lineups, matchup, rest, usage, weather where applicable.
3. Simulate outcomes with documented distributions, seeded reproducible runs, scenario sensitivity and uncertainty bands. Never claim simulation ran if output absent.
4. Calibrate probabilities on timestamped out-of-sample settled events. Record Brier/log loss and sample sizes; never infer calibration from collected contracts.
5. Read Kalshi bid/ask and depth, order fees, and sportsbook no-vig reference probabilities. Quote timestamps and market capacity matter.
6. Compute p_model, p_market, price gap, net EV per contract, and capped Kelly fraction only with verified fees and execution assumptions. Prediction ranking and value ranking are distinct.
7. Archive pregame forecasts, execution-price snapshots, settled outcomes, CLV and per-sport calibration; monitor drift.
8. Produce `data/kalshi-advanced-picks.json` with explicit fields: generated_at, fixture_id, ticker, side, model_probability, probability_interval, model_version, feature_sources, feature_freshness, simulations, scenario_results, calibration, kalshi_ask, available_size, fee_basis, net_ev, sportsbook_consensus, rank_prediction, rank_value, eligibility_reasons.
9. Main page: top advanced winners ticker and detailed ranked predictions with reasons and risks. Research tab: all contracts, baseline references, diagnostics, and model history.

## Non-negotiable acceptance tests
- A pick tagged ADVANCED must include validated sport-specific features, simulation artifact, and provenance; no boolean self-assertion without evidence.
- No upcoming matched fixtures may be silently dropped due to alias or event-date mismatch.
- End-to-end fixture test uses independent known inputs, predicts both YES and NO, verifies odds and fee math, and renders a nonempty mobile board.
- On pipeline failure preserve last-known data but mark timestamps stale; never silently substitute market implied odds for model probability.
- Never conflate high win probability with positive net expected value; no guarantee of wins.

## Current implementation gap
The existing `feed/model_market_decisions.json` contains provisional baseline sources (e.g. score-margin shrinkage) rather than proof of complete advanced simulation and matchup evidence. Do not promote these to ADVANCED until validated outputs exist.
