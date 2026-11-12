"""Validate WR betting-feed picks. Only complete, fresh, independently simulated picks pass."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path

REQUIRED = ("player_name", "team", "market", "side", "book", "line", "american_odds", "model_probability", "simulations", "verified_at")
MARKETS = {"receptions", "receiving_yards", "receiving_touchdowns", "targets"}
SIDES = {"over", "under"}

def validate(p, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    if not isinstance(p, dict) or any(k not in p for k in REQUIRED):
        return False, "missing required fields"
    if any(not isinstance(p[k], str) or not p[k].strip() for k in ("player_name", "team", "market", "side", "book")):
        return False, "invalid identity or market"
    if p["market"] not in MARKETS or p["side"] not in SIDES:
        return False, "unsupported market"
    for key in ("line", "american_odds", "model_probability"):
        if isinstance(p[key], bool) or not isinstance(p[key], (int, float)) or not math.isfinite(p[key]):
            return False, "invalid numeric " + key
    odds = p["american_odds"]
    if odds != int(odds) or abs(odds) < 100 or odds == 0 or not 0 < p["model_probability"] < 1 or p["line"] < 0:
        return False, "invalid odds/probability/line"
    if type(p["simulations"]) is not int or p["simulations"] < 1000:
        return False, "insufficient simulation count"
    try:
        verified = dt.datetime.fromisoformat(p["verified_at"].replace("Z", "+00:00"))
        if verified.tzinfo is None or not dt.timedelta(0) <= now - verified.astimezone(dt.timezone.utc) <= dt.timedelta(minutes=15):
            return False, "stale or future timestamp"
    except (ValueError, TypeError, AttributeError):
        return False, "invalid timestamp"
    if p.get("injury_verified") is not True or p.get("game_status_verified") is not True or p.get("projection_source") in (None, "") or p.get("simulation_source") in (None, ""):
        return False, "missing independent verification"
    return True, "verified"

def process(payload, now=None):
    picks = payload.get("picks", []) if isinstance(payload, dict) else []
    if not isinstance(picks, list):
        raise ValueError("picks must be an array")
    result = []
    for p in picks:
        ok, reason = validate(p, now)
        entry = dict(p) if isinstance(p, dict) else {}
        entry["status"] = "BETTING_READY" if ok else "UNAVAILABLE"
        entry["validation_reason"] = reason
        if ok:
            prob = p["model_probability"]
            odds = p["american_odds"]
            net = odds / 100 if odds > 0 else 100 / -odds
            entry["implied_probability"] = 1 / (1 + net)
            entry["expected_value_per_unit"] = prob * net - (1 - prob)
            entry["fair_american_odds"] = round(-100 * prob / (1 - prob) if prob >= .5 else 100 * (1 - prob) / prob)
        result.append(entry)
    return {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "picks": result}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    payload = json.loads(Path(args.input).read_text())
    Path(args.output).write_text(json.dumps(process(payload), indent=2) + "\n")

if __name__ == "__main__":
    main()
