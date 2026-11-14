# PFL Moneyline & Total Rounds — implementation contract

Status: specification only; no live odds, projections, or simulations are claimed to be operational.

## Scope
New PFL tab consistent with existing UFC and mobile design. Only moneyline and total-round markets. Internal method-of-victory probabilities support duration modeling but are not offered as bets.

## Data ingestion
- Official PFL events/results and bout metadata, verified fighter records and round lengths.
- UFCStats for fighters with UFC histories; PFL-specific statistics from verified public records; retain source, retrieved_at, confidence, and mapping.
- Public odds snapshots where licensed/available; Onyx remains unverified until user supplies line or legitimate feed.
- Canonical fighter IDs and aliases; never silently match names; no stale odds; track bout cancellations, replacements, event timezone, 3/5-round rules and settlement rules.
- Do not treat a lack of public data as zero performance.

## Modeling
- Moneyline: hierarchical opponent-adjusted fighter strength, Elo/Bayesian shrinkage, recency, age, layoff, weight class, promotion strength, strike differential, takedown/control, submission threat, quality of opposition, short notice and camp context.
- Duration: competing-risk round-by-round hazards for KO/TKO, submission, decision; survivor S(t) at exact sportsbook thresholds; calibrate by scheduled 3/5 rounds. Model method and time dependence, not independent round Bernoulli trials.
- Monte Carlo >=50,000 reproducible seeded simulations per bout when validated inputs exist; estimate uncertainty intervals and effective sample sizes.
- Market comparison: remove bookmaker vig for reference only; calculate fair American odds, EV per $1, edge and Kelly fraction with conservative cap. Flag correlated ML + totals; never multiply probabilities for same-fight parlays.
- Backtest walk-forward with temporal leakage prevention, log loss/Brier, calibration bins, closing-line value, duration Brier, coverage and source freshness. Hold out recent events.

## UI
- PFL tab, upcoming card ET order, matchup cards, predicted ML both sides, O/U at exact available lines, book/price/time/source, win and over/under probabilities, fair odds, EV, confidence, simulation status.
- Diamond Plays only when sample adequacy, fresh source, simulation, calibration and EV thresholds pass. Explicit COMPLETE/PASS/UNAVAILABLE/UNVERIFIED for each check.
- Filters: upcoming/event, weight class, ML/totals, value, underdog; interactive fight detail with matchup radar, finish hazard chart, historical fights and line movement.
- Empty state: "No verified betting-ready PFL picks" rather than placeholder picks.
- Reuse existing shared odds ingestion, data mapping, simulator, model governance, caching and styling where compatible; don't duplicate navigation.

## Acceptance tests
1. 3-round fight O/U 2.5 resolves at 12:30 elapsed, 5-round fight O/U 4.5 at 22:30; exact-boundary pushes follow book rules.
2. Two ML probabilities sum to 1 and over/under probabilities sum to 1 for each threshold (excluding explicit push mass).
3. Fight replacement invalidates predictions and stale lines.
4. Fighter aliases resolve deterministically or block predictions.
5. No prediction if missing verified opponent, schedule, round length, market line or required stats.
6. Simulations reproducible with fixed seed; convergence checks and calibration tests.
7. No fake live feeds or odds; show UNVERIFIED for missing Onyx lines.
8. Mobile layout matches existing theme, navigation and accessible interactive elements.
9. Validate CI and production build before merge.


## Verified source discovery — 2026-11-14
Source candidates; do not claim integration until endpoints, legal access, completeness and freshness are tested.

| Source | Use | Verification |
| --- | --- | --- |
| https://pflmma.com/news | Official event announcements, weigh-ins, cancellations, fighter news | Primary official authority; inspect event timestamp |
| https://pflmma.com/all-fighter/taylor-lapilus | Fighter profile and results | Official profile example |
| https://pflmma.com/news/professional-fighters-league-introduces-independent-fighter-rankings-powered-by-combat-registry | Rankings context | Rankings are journalist votes, not an independent quantitative rating |
| https://docs.citoapi.com/pfl-api/ | Candidate events, bouts, scheduled rounds, fighter IDs and UFC linkage | Third-party API; verify authentication, pricing, licensing, completeness and latency; provider says no PFL strike/round stats |
| http://ufcstats.com | UFC bout-level and round-level historical stats for crossover fighters | UFC history only; not PFL bout statistics |
| https://www.sherdog.com | Cross-promotion records, opponent histories and finishes | Verify permitted access and cross-check official results |
| https://www.tapology.com | Event changes, bout records and fighter identities | Verify permitted access and cross-check official results |
| https://www.espn.com/mma/ | News, reporting, result corroboration | Secondary reporting |

### News/event monitor
- Event announced -> card versioned; matchup and scheduled rounds confirmed.
- Fighter withdrawal/replacement, weigh-in miss, catchweight, title-status change -> invalidate affected model/market.
- Monitor official news and weigh-ins at pre-event intervals; retain timestamps and article URLs.
- Classify announcements by promotion and sport; exclude boxing cards from MMA projections.
- Record rumor vs confirmed status; only official confirmation can change the canonical card.
- Do not label API or news monitoring active before an actual scheduled workflow exists.

### Today's integration fixture
PFL Dubai November 14 2026 official weigh-ins: Nemkov vs Bilostenniy, Habirora vs El Dafrawy, Popov vs Rahmani, Pettis vs Goto, Rock vs Hughes. Use only as a historical test fixture after event completion; do not assert live odds or forecast outputs.
