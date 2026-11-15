# Kenny's Sports Lab — Agent Development Contract

This file governs coding work in this repository. Follow it on every task, including a brief "continue" request. Inspect the latest branch, PRs, workflow runs and actual code before changing anything.

## Objective
Build and maintain an automated, mobile-friendly **betting model**, not a research-only dashboard. Prioritize verifiable upcoming events, independent probabilities, fair odds, expected value, Monte Carlo where supported, injury/lineup inputs, matchup data, and actionable betting outputs. Never invent data or describe unverified projections as betting-ready.

## Execution rules
1. **Execute rather than narrate.** For "continue", resume the latest verified repository state and tackle the next concrete blocker; do not ask the user to repeat established requirements.
2. **Batch related work.** Trace the entire affected path (source → collection → normalization → validation → model → published feed → UI) before editing. Implement related fixes together rather than many tiny PRs.
3. **Diagnose first.** Read failing workflow logs and reproduce errors. Never guess at a failure from a green/red badge alone. Check syntax, imports, fixtures, file paths, contracts and edge cases.
4. **Test before reporting.** Run applicable Python/JS syntax checks, unit/integration tests and CI; investigate failures, repair, and rerun. Validate GitHub Pages mobile behavior when possible. A passing UI test is not proof of fresh data.
5. **Merge only after verification.** Use PRs, inspect required checks, and merge verified changes. Report exact PR/commit and what was actually tested. Do not claim deployed or fixed without evidence.
6. **Preserve working behavior.** Avoid removing markets, models, modules, navigation, historical data, or existing metrics unless explicitly requested. Add regression tests for past failures.
7. **Reuse existing integrations.** Audit available free feeds, scripts, API quotas and previously implemented models before adding providers, duplicate workflows or paid dependencies.
8. **Automate safely.** Prefer scheduled collection and a consolidated orchestrator; no routine manual refresh buttons. Never expose GitHub/API secrets in client-side code. A static GitHub Pages button cannot securely dispatch privileged workflows by itself.
9. **Fail closed on data integrity.** Distinguish COMPLETE, PASS, UNAVAILABLE and UNVERIFIED with reasons. Reject empty, stale, completed-event, malformed or mismatched data for betting recommendations. Preserve prior good snapshots without falsely labeling them current.
10. **Report results concisely.** State what changed, test/CI outcome, deployment status and any genuine external dependency. Do not repeatedly present outstanding task lists instead of working on them.

## Betting-specific checks
- Verify event date/time (ET), sport, player/team mapping, settlement market, actual offered line and sportsbook; Onyx is primary when supplied, DK/FD reference only.
- Include both sides of ML/spread/total where applicable, fair odds, EV, uncertainty, simulation assumptions, and injury/lineup sensitivity.
- Do not fabricate Monte Carlo results. Mark simulation UNAVAILABLE when required inputs are missing.
- Avoid duplicate players, teams or incompatible legs in parlays; model correlation instead of assuming independence without disclosure.
- UFC/PFL: only upcoming fights, predicted winner and round/total recommendation where supported, clearly marked model confidence; do not treat a favorite as automatically the model pick.
- NFL: WR/CB, man/zone, routes, target share, first reads, end-zone usage and injuries when verified.
- NBA/NHL/NCAAB: current matchups, odds, starters/goalies where applicable, usage and model projections; preserve existing betting tools.

## Definition of done
A task is done only when (a) the source and transformation are correct, (b) relevant automated checks pass, (c) the user-facing feature works with real verified data or explicitly states why not, (d) regressions are checked, and (e) deployment/merge is verified. If blocked by unavailable credentials, provider quotas or external infrastructure, implement all safe preparatory work, document the exact blocker and never simulate success.

## Communication
The user prefers **large batches, no repetitive approvals, no shortcut patches, and results over status narration**. Prioritize completing fixes rather than repeatedly asking to continue. Never silently claim background work is running after the turn ends.
