# PFL data acquisition matrix
Updated 2026-11-14. Candidate sources are not automatically connected or licensed for bulk reuse.

| Source | Data | Access / caveat | Priority |
| --- | --- | --- | --- |
| PFL official (pflmma.com) | schedule, cards, weigh-ins, fighter and event news | Check reuse terms, corroborate changes | P0 |
| Cito PFL API (citoapi.com/docs/api/pfl/) | PFL events since 2018, results, methods, rounds, finish times, fighter identities, live status | Requires API key; free 30-day historical window; free-tier historical window only; never upgrade or bypass paid historical access; no PFL striking, takedown or control statistics | P0 |
| UFCStats (ufcstats.com) | UFC bouts of crossover fighters, significant strikes, takedowns, control where available | Not PFL statistics; promotion transfer bias | P1 |
| Sherdog | cross-promotion records, methods and fight histories | Verify site terms and fighter mapping | P1 |
| Tapology | fight cards, records, opponents, replacements | Verify access permissions and independent corroboration | P1 |
| ESPN MMA | card reporting and news | News corroboration; not an authoritative odds feed | P1 |
| FightBook MMA | PFL card updates, weigh-in reporting | Secondary; compare against official announcements | P2 |
| Sportsbook / licensed odds provider | ML and total rounds opening/current lines | Availability, market naming, settlement and licensing must be verified; Onyx unverified | P0 |

## Pipeline
- Server-side API requests only. Store API keys as GitHub Actions secrets, never in public pages.
- Ingest event metadata and results, then fighter histories and round finish times when authorized.
- Store source, retrieval time, IDs, verification state, and provider coverage window.
- Detect card changes and distinguish pending results from completed bouts.
- Reject missing round times for half-round totals; never fill absent strike stats with zero.
- Do not auto-activate picks without fresh prices, calibrated independent projections, and 50k verified simulations.
- Current integration only implements a **Cito event snapshot adapter**. It has not fetched live data without a configured key.

## Mandatory free-only policy (2026-11-14)
- No paid API plans, paid trials, paywall circumvention, proxy rotation to evade limits, or unauthorized scraping.
- Free-tier APIs may be used only within their documented quotas, with caching and backoff.
- Sources requiring payment are excluded from automated acquisition.
- Do not substitute absent paid data with fabricated values; label UNAVAILABLE.
- Reuse existing authorized UFC crossover data with clear promotion provenance; never label it PFL fight statistics.
