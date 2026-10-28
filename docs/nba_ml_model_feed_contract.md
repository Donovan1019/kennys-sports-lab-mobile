# NBA Moneyline model feed contract

Optional endpoint: `feed/nba_ml_predictions.json`. No fake default predictions should be committed.

Example structure (illustrative schema only, not real predictions):

```json
{
  "status": "validated",
  "sport": "basketball_nba",
  "generated_at": "ISO-8601 UTC timestamp",
  "calibration_passed": true,
  "predictions": [
    {
      "event_id": "match the current odds event_id",
      "team": "match the current odds selection",
      "date_et": "YYYY-MM-DD",
      "win_probability": 0.5
    }
  ]
}
```

Producer requirements: independent team/player inputs, injury/lineup and rest handling, leak-free walk-forward validation, calibration and Brier-score reporting, versioned training window, and a trustworthy validation job that controls status and calibration_passed. The browser cannot independently verify the producer's assertions.

A complete set of validated probabilities unlocks model-probability simulations. The UI still marks EV **illustrative and NOT BET ELIGIBLE** because sportsbook parlay quotes, leg correlation, injury and lineup checks are not independently verified. Do not interpret the synthetic multiplied leg prices as an executable parlay quote.

Postgame grading remains unavailable until a trustworthy results feed and archival predictions are connected. The existing code does not create such a feed or backtest.
