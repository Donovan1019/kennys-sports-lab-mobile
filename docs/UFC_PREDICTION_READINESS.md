# UFC prediction readiness — acceptance gates

The fight comparison UI is merged. This checklist governs the transition from research estimates to betting forecasts.

## Data integrity
- Join fighters using stable identifiers; audit ambiguous name matches and fight duplicates.
- Prevent future outcomes and post-fight statistics entering pre-fight features.
- Track source, observation time, completeness, and age for each field.
- Verify bout date, scheduled rounds, weight class, opponent, and availability.

## Winner model
- Build a pre-fight baseline (Elo and prior fight history), then a regularized statistical model.
- Use chronological train/validation/test splits, walk-forward evaluation, and probability calibration.
- Report Brier score, log loss, reliability by probability bucket, and performance against no-vig market baseline.
- Separate model favorite from positive-EV recommendation; compute EV using verified offered odds.

## Volume props
- Estimate expected fight duration and fighter/opponent-adjusted striking and takedown rates.
- Fit count distributions with overdispersion and zero inflation where appropriate.
- Validate MAE, interval coverage, and hit probabilities at historical offered lines.

## Finish/method/round
- Estimate mutually consistent win by KO/TKO, submission, decision and finish timing.
- Require probabilities to sum to one across exhaustive outcomes.
- Backtest log loss/Brier and uncertainty before displaying recommendation status.

## Market data
- Treat https://fightodds.io/odds as a comparison/research website; verify permitted API or data access before automating ingestion.
- Retain existing DraftKings/FanDuel snapshot integration; enforce quote timestamps, exact fighter/market/line/side and two-sided no-vig where applicable.
- Never call a historical quote live or manufacture missing prop lines.

## Release gates
- Every card shows both fighter projections, model confidence, source freshness and exact market context.
- Use 'research estimate' for uncalibrated outputs; only publish betting recommendations after out-of-sample evaluation and live quote checks.
- CI must test identity matching, data leakage, probability coherence, calibration reports, market matching, and mobile rendering.
- Maintain abstention for insufficient data; never substitute fabricated accuracy.
