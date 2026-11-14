# PFL Analytics Pro — large-batch roadmap

## Scope
Only moneyline and total-round betting markets. Keep the existing Kenny's Lab dark/gold shared styles, mobile-first navigation, and interactive charts. No unsupported prop markets.

## Data architecture
- Canonical event, bout, fighter, opponent, result and round-timing records with provenance and UTC timestamps
- PFL official card / weigh-in / withdrawal monitoring; promotion-specific identity aliases and cross-promotion records
- Explicit source rights and provider availability checks; no assumed free API access
- Snapshot market prices by book, timestamp, bet rules, event, and total threshold
- Distinguish published statistics, model-derived estimates and missing fields

## Models
1. Hierarchical opponent-strength ratings with promotion uncertainty, time decay and sample-size shrinkage
2. Style and matchup interaction: wrestling, control, striking, durability, age, inactivity and scheduled rounds, only where validated
3. Competing-risk minute-level KO/submission/decision survival model, including timing within each round for x.5 totals
4. Monte Carlo 50k+ with fixed seeds and uncertainty intervals; avoid unsupported independence for same-fight parlays
5. Value ranking using fair odds, no-vig reference and estimated EV with model confidence gates

## Interactive product
- Fighter matchup cards, trend windows, confidence explanations, head-to-head comparisons and drill-down source links
- Moneyline and totals line comparison, implied probability, fair price, EV and line history
- Parlay generator Gold/Silver/Bronze, 2–5 legs, risk audit, adjustable stake, combined price and joint simulation
- Market mispricing / false favorite / underdog watchlists with evidence and explicit data limitations
- Source freshness and fight-status alerts, versioned projection archives, calibration, CLV and ROI dashboards

## Release gates
- No bet-eligible output without verified bout identity, scheduled rounds, current odds, fight status, calibrated model and simulation
- Backtest on chronologically held-out fights, report Brier, log loss, calibration by market, ROI and uncertainty
- Check no duplicate nav, dead links, stale odds, fake percentages or conflicting parlay legs
- Run unit, browser interaction, mobile responsive and end-to-end tests before merge
