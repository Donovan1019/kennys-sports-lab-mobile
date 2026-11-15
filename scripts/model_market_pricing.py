"""Independent model-vs-market evaluation shared across sports.

No sportsbook-implied probability is substituted for an independent model estimate.
Price verification is separate from the ability to generate a projection.
"""
from datetime import datetime, timezone
from math import isfinite


def decimal_odds(american):
    if isinstance(american, bool) or not isinstance(american, (int, float)) or not isfinite(american) or american == 0 or abs(american) < 100:
        raise ValueError("Invalid American odds")
    return 1 + (american / 100 if american > 0 else 100 / -american)


def implied_probability(american):
    return 1 / decimal_odds(american)


def no_vig_probabilities(american_prices):
    """Normalize implied probabilities of an exhaustive, mutually exclusive market."""
    if len(american_prices) < 2:
        raise ValueError("At least two complete outcomes are required")
    raw = [implied_probability(price) for price in american_prices]
    total = sum(raw)
    if total <= 0:
        raise ValueError("Invalid market")
    return [p / total for p in raw]


def fair_american(probability):
    if not 0 < probability < 1 or not isfinite(probability):
        raise ValueError("Probability must be between zero and one")
    return round(-100 * probability / (1 - probability) if probability >= .5 else 100 * (1 - probability) / probability)


def expected_value(probability, american):
    if not 0 < probability < 1 or not isfinite(probability):
        raise ValueError("Independent probability required")
    return probability * decimal_odds(american) - 1


def evaluate_uncertainty(model_probability, probability_low, probability_high, american, *,
                         independent_model=False, price_verified=False, event_verified=False,
                         model_verified=False, odds_timestamp=None, now=None,
                         max_price_age_minutes=30):
    """Conservative edge test using a validated model probability interval.

    The interval must be independently estimated and validated upstream.
    A positive point EV alone does not imply a robust betting edge.
    """
    base = evaluate(model_probability, american, independent_model=independent_model,
                    price_verified=price_verified, event_verified=event_verified,
                    model_verified=model_verified, odds_timestamp=odds_timestamp,
                    now=now, max_price_age_minutes=max_price_age_minutes)
    if base["bet_status"] not in ("BETTING_READY", "NO_VALUE"):
        return base
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not isfinite(x)
           for x in (probability_low, probability_high)):
        return {**base, "bet_status": "PROVISIONAL", "reason": "Model uncertainty interval unavailable"}
    if not (0 < probability_low <= model_probability <= probability_high < 1):
        return {**base, "bet_status": "PROVISIONAL", "reason": "Invalid model uncertainty interval"}
    lower_ev = expected_value(probability_low, american)
    upper_ev = expected_value(probability_high, american)
    return {**base, "probability_interval": [probability_low, probability_high],
            "ev_interval": [lower_ev, upper_ev],
            "bet_status": "BETTING_READY" if lower_ev > 0 else "NO_ROBUST_EDGE",
            "reason": "Positive EV across model uncertainty interval" if lower_ev > 0
                      else "Edge does not survive model uncertainty"}


def evaluate(model_probability, american=None, *, independent_model=False,
             price_verified=False, event_verified=False, model_verified=False,
             critical_data_error=False, odds_timestamp=None, now=None,
             max_price_age_minutes=30):
    """Return distinct projection and execution statuses, never fabricate a bet edge."""
    if critical_data_error or not independent_model or not model_verified or not isinstance(model_probability, (int, float)) or isinstance(model_probability, bool) or not isfinite(model_probability) or not 0 < model_probability < 1:
        return {"model_status": "BLOCKED", "bet_status": "BLOCKED", "reason": "No valid independent model projection"}
    result = {"model_status": "READY", "bet_status": "PROVISIONAL",
              "model_probability": model_probability, "fair_odds": fair_american(model_probability)}
    if not event_verified:
        result["reason"] = "Upcoming event not verified"
        return result
    if american is None or not price_verified or not odds_timestamp:
        result["reason"] = "Offered price not verified"
        return result
    try:
        now = now or datetime.now(timezone.utc)
        quote = datetime.fromisoformat(odds_timestamp.replace("Z", "+00:00"))
        age = (now - quote).total_seconds() / 60
        if quote.tzinfo is None or now.tzinfo is None or age < 0 or age > max_price_age_minutes:
            result["reason"] = "Price timestamp stale or invalid"
            return result
        implied = implied_probability(american)
        ev = expected_value(model_probability, american)
    except (ValueError, TypeError, AttributeError, OverflowError):
        result["reason"] = "Invalid price or timestamp"
        return result
    result.update({"bet_status": "BETTING_READY" if ev > 0 else "NO_VALUE",
                   "offered_odds": american, "break_even_probability": implied,
                   "edge_probability_points": 100 * (model_probability - implied),
                   "expected_value": ev, "price_age_minutes": age,
                   "reason": "Positive model EV" if ev > 0 else "No positive edge at offered price"})
    return result
