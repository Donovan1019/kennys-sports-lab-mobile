# PropsMadness sitemap → Kenny's Sports Lab design contract

Reference: https://propsmadness.com/sitemap
Checked: 2026-11-06. Recheck this URL and each affected reference page before **every** UI change. Do not substitute palette-only changes for structural fidelity.

## Reference hierarchy
- NBA Player breakdown: https://propsmadness.com/nba — player selection, market selection, suggested/all filters, season, Graph / Shooting / Similar / Types, shooting zones, play type, shot type and comparable players.
- NBA Explore: https://propsmadness.com/nba/props/points — market rail, search players/teams, game filter, market filter, L5/L10/L15/Season windows, offers-only, sortable multi-column results.
- NBA market groups: Scoring (Points, Assists, Rebounds, Threes), Combos (Pts+Ast, Pts+Reb, Reb+Ast, PRA, double/triple double), Fantasy (PrizePicks/Underdog), 1Q, 1H, Defense, Other.
- NFL Player breakdown: https://propsmadness.com/nfl — passing/receiving/rushing/scoring/defense/fantasy/quarter/half, injuries, player-vs-defense and similar players; NFL Explore + cheat sheet.
- WNBA: player breakdown and analogous grouped market pages; MLB: pitcher and batter breakdown and market pages.
- Resources: parlay calculator and league-specific glossaries. Kenny's extra NHL/UFC/PrizePicks, Diamond Plays, simulations and parlays remain first-class native modules.

## Implementation rules
1. Inspect reference sitemap, actual destination page, and original screenshots before modifying the corresponding Kenny page.
2. Match information architecture, navigation placement, tab hierarchy, card structure, filters, chart geometry, typography, spacing and mobile behavior. Do not copy proprietary code, imagery or brand assets.
3. Preserve all existing working sports model, parlay, and feed logic; make styling and routing changes separately from predictive changes.
4. Display missing stats/odds as unavailable. Do not invent sportsbook lines, injury reports, shot locations, opponent defense rankings or historical hit rates.
5. Verify navigation targets, responsive behavior, visible states, tests and Pages deployment; record which screenshot/reference pages were inspected in each PR.
6. Reference-only modules not supported by Kenny's data must be labeled **Data unavailable**, not filled with fake examples.

## Current gap register
- NBA Explore: grouped sitemap rail and explicit availability state — in progress.
- NBA breakdown: four existing tabs; shooting zones, opponent defense, true play types and line-based hit-rate chart need verified inputs.
- NFL Explore: full grouped market navigation and injury panel parity pending.
- WNBA: grouped market navigation parity pending.
- MLB: not yet implemented; NHL/UFC require their own reference-adapted structures.
- Parlay calculator/glossary: sitemap resource parity pending.

Keep this file as a change-control checklist and update it with every design PR.

## Batch 2026-11-06: NBA/NFL/NHL only
Source checked again: https://propsmadness.com/sitemap (NBA combo PRA is listed as Pts+Reb+Ast; NFL categories Passing/Receiving/Rushing/Scoring/Defense/1Q/1H).
- NBA: prominent PRA shortcut wired to existing verified PRA historical game-log selector; no synthetic lines.
- NFL: display reference-aligned market groups; no unsupported selection buttons.
- NHL: **not present in PropsMadness sitemap**. Adapt its hierarchy and card system to hockey-specific skater/goalie/game markets, without pretending these are PropsMadness pages.
- Keep UFC/WNBA untouched this batch.
- Next: visually verify iPhone widths and reference screenshot parity, then connect verified NFL/NHL market-specific data.

## Batch 2026-11-06: shared player breakdown graphs
Reference hierarchy: NBA breakdown Graph/Shooting/Similar/Types and NFL player breakdown from the sitemap; NHL follows analogous presentation because reference site has no NHL page.
- Shared NBA/NFL/NHL Player Stats now include L5/L10/L15/L30 selection, top-ranked player historical chart, descriptive average and recorded sample size.
- NHL Points is calculated only when both Goals and Assists are present in the same recorded game.
- NHL SOG remains explicitly unavailable in the current published player game-log feed (source flags SOG unverified); do not show fabricated shots.
- No betting hit-rate coloring without a verified sportsbook line.
- Still pending: actual mobile screenshot comparison, NFL position-specific detailed breakdown, NHL verified SOG feed, historical odds line overlays.

## Batch 2026-11-06: player-selectable charts
- Compared design against NBA/NFL breakdown architecture recorded above. Added player selector to shared historical stats chart so it no longer always displays the highest-average player.
- Deployment of previous batch #720 verified successful (Pages run 42310830810).
- Existing Market Math Tests failed independently of this UI batch: NBA minutes-adjusted MAE expected 5.125 but actual 5.25; NFL stats fixture expected DATA_PRESENT_UNVERIFIED but returned BLOCKED. Do not alter safety gates merely to turn CI green. Investigate separately.

## Batch 2026-11-07: historical opponent identity beneath chart dates
- Preserve the original mobile game-log bars, stat numbers, and date labels; append a compact opponent logo slot below each date.
- Only use verified per-game opponent abbreviations. NBA and NHL ESPN boxscore imports and official NHL imports now preserve opponent identity for newly parsed games; NFL importer accepts an opponent field only if the nflverse source provides one.
- Existing cached historical records do not automatically gain missing opponent fields. Backfill must use verified event metadata, not player current team or guessed schedules.
- Broken image URLs fall back to opponent abbreviations; absent verified opponent is marked unavailable.
- Focused workflow checks chart JavaScript syntax and NBA/NFL/NHL opponent extraction. Verify mobile iPhone rendering and CI before merge.
