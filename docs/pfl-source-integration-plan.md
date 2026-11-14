# PFL betting-data source integration plan

Last reviewed: 2026-11-14

## Source hierarchy and usage

1. **Cito PFL API** (authenticated, already operational): `https://docs.citoapi.com/docs/api/pfl/`. Expand existing `CITO_API_KEY` integration to `/pfl/fighters/{slug}`, `/pfl/fighters/{slug}/fights`, `/pfl/h2h?fighter1=...&fighter2=...`, and `/mma/fighters/{slug}` when available under the existing plan. UFC fighter links are explicit `ufcFighterSlug`. Respect rate limits and avoid exhausting free quota. Do not assume every endpoint is enabled until tested.
2. **ESPN MMA**: `https://www.espn.com/mma/`. Cross-check cards, fighter identity, records and results. Check access terms before automated extraction.
3. **Tapology**: `https://www.tapology.com/`. Independent career history, promotion results, opponents, finish patterns, tale-of-the-tape. Review access permissions; do not bypass anti-bot restrictions, scrape behind logins, or purchase third-party scraping services.
4. **Official PFL**: `https://pflmma.com/`. Primary promotion confirmation for events, bout announcements, cancellations and weigh-ins.
5. **Fourounce PFL stats**: `https://fourounce.com/stats/pfl/all`. Candidate source for significant strikes, wrestling and control rates. Confirm methodology, provenance, permissions, per-fighter coverage and sample size before quantitative use.
6. **MMA Fighting PFL results**: `https://www.mmafighting.com/fight-results/pfl`. Independent results and method/round/time checks.

## Critical data caveat

Cito explicitly documents **no official PFL significant strike, takedown, control-time, or round-by-round stats**. The PFL results API should not be represented as supplying those metrics. Stats from other promotions can be transferred only with an explicit cross-promotion adjustment, sample-size weighting and uncertainty.

## Join and validation requirements

- Canonical fighter key: Cito fighter slug, explicit UFC slug crosswalk; other source IDs retained separately.
- No fuzzy-name auto-merges for ambiguous identities; surface unresolved mappings.
- Join event by date, promotion, and participants; date-only matching is candidate evidence, not proof.
- Preserve per-field source URL, retrieval timestamp, sample size and confidence.
- No inferred scheduled rounds for the two flagged bouts: `pfl-401914114`, `pfl-401919462`.
- Keep PFL duration markets blocked without verified rounds and settlement rules.
- Never present a live bet without timestamped sportsbook price, verified fighter/bout status, calibrated probability, simulated distribution, and positive EV.
- A successful data workflow does **not** imply betting readiness.

## Next acquisition batch

1. Fetch fighter profiles and PFL histories for upcoming-card slugs from Cito, with rate-limit aware sequential requests and partial-error reporting.
2. Build identity crosswalk and historical outcome feature tables (finish rate, time-to-finish, recency, opponent strength with shrinkage).
3. Validate official PFL and ESPN event cards, then Tapology histories, subject to site terms.
4. Investigate licensed or permitted Fourounce data access for PFL striking/wrestling metrics.
5. Add verified odds connector only after identifying an accessible, legal, free odds feed. Never manufacture odds or treat third-party predictions as sportsbook prices.
6. Run tests, audit coverage, and only then enable Monte Carlo/EV markets.
