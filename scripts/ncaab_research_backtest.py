#!/usr/bin/env python3
"""NCAAB point-in-time historical research; no betting probability or EV output."""
import collections
import datetime as dt
import json
import math
import pathlib
import statistics

SOURCE = pathlib.Path("data/ncaab_espn_history.json")
OUTPUT = pathlib.Path("data/ncaab_research.json")
MIN_HISTORY = 5

def season_key(date):
    year, month = map(int, date.split('-')[:2])
    return year + (1 if month >= 7 else 0)

def team_key(row):
    return str(row.get("id") or "").strip()

def eligible_game(g):
    teams = g.get("teams", [])
    return (len(teams) == 2 and all(
        team_key(t) and isinstance(t.get("points"), (int, float))
        and isinstance(t.get("possessions_est"), (int, float))
        and 35 < t["possessions_est"] < 130 and 0 <= t["points"] < 250
        for t in teams))

def evaluate(games):
    history = collections.defaultdict(list)
    current_season = None
    predictions = []
    for g in sorted(games, key=lambda x: (x.get("date", ""), x.get("event_id", ""))):
        if not eligible_game(g):
            continue
        a, b = g["teams"]
        # Predictions for an entire date are computed from strictly earlier dates.
        day = g["date"]
        predictions.append((day, g, a, b))
    by_day = collections.defaultdict(list)
    for day, g, a, b in predictions:
        by_day[day].append((g, a, b))
    evaluated = []
    for day in sorted(by_day):
        season = season_key(day)
        if current_season != season:
            history.clear()  # Prevent previous-season rosters and form from contaminating estimates.
            current_season = season
        # No same-day final scores may enter the feature set.
        for g, a, b in by_day[day]:
            aa, bb = history[team_key(a)], history[team_key(b)]
            if len(aa) < MIN_HISTORY or len(bb) < MIN_HISTORY:
                continue
            ap = statistics.mean(x["pace"] for x in aa[-15:])
            bp = statistics.mean(x["pace"] for x in bb[-15:])
            pace = (ap + bp) / 2
            aoff = statistics.mean(x["off"] for x in aa[-15:])
            adef = statistics.mean(x["def"] for x in aa[-15:])
            boff = statistics.mean(x["off"] for x in bb[-15:])
            bdef = statistics.mean(x["def"] for x in bb[-15:])
            # Unadjusted efficiency blending: diagnostic baseline only.
            a_est = pace * (aoff + bdef) / 200
            b_est = pace * (boff + adef) / 200
            evaluated.append({"date": day, "event_id": g["event_id"],
                              "a_id": team_key(a), "b_id": team_key(b), "season": season,
                              "a_actual": a["points"], "b_actual": b["points"],
                              "a_pred": round(a_est, 3), "b_pred": round(b_est, 3),
                              "total_actual": a["points"] + b["points"],
                              "total_pred": round(a_est + b_est, 3)})
        for g, a, b in by_day[day]:
            pace = (a["possessions_est"] + b["possessions_est"]) / 2
            for t, opponent in ((a, b), (b, a)):
                history[team_key(t)].append({"pace": pace,
                    "off": 100 * t["points"] / t["possessions_est"],
                    "def": 100 * opponent["points"] / opponent["possessions_est"]})
    return evaluated, history

def summarize(rows):
    if not rows:
        return {"status": "INSUFFICIENT_HISTORY", "games": 0, "minimum_prior_games_per_team": MIN_HISTORY,
                "margin_mae": None, "season_evaluations": {}, "sample_sufficient": False,
                "minimum_evaluations_for_research": 200}
    errors = [r["total_pred"] - r["total_actual"] for r in rows]
    margin_errors = [(r["a_pred"] - r["b_pred"]) - (r["a_actual"] - r["b_actual"]) for r in rows]
    by_season = collections.Counter(r["season"] for r in rows)
    return {"status": "RESEARCH_BASELINE", "games": len(rows),
            "total_mae": round(statistics.mean(abs(e) for e in errors), 3),
            "total_rmse": round(math.sqrt(statistics.mean(e * e for e in errors)), 3),
            "total_bias": round(statistics.mean(errors), 3),
            "margin_mae": round(statistics.mean(abs(e) for e in margin_errors), 3),
            "season_evaluations": dict(sorted(by_season.items())),
            "sample_sufficient": len(rows) >= 200,
            "minimum_evaluations_for_research": 200,
            "minimum_prior_games_per_team": MIN_HISTORY}

def main():
    source = json.loads(SOURCE.read_text())
    unique = {}
    for g in source.get("games", []):
        if g.get("event_id"):
            unique[g["event_id"]] = g
    rows, history = evaluate(list(unique.values()))
    output = {"provider": "ncaab-research-baseline", "source": "espn-public",
              "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "source_fetched_at": source.get("fetched_at"),
              "latest_evaluation_date": max((r["date"] for r in rows), default=None),
              "latest_source_game_date": max((g.get("date", "") for g in unique.values()), default=None),
              "historical_games": len(unique), "usable_games": sum(eligible_game(g) for g in unique.values()),
              "teams_observed": len(history), "walk_forward": summarize(rows),
              "research_only": True,
              "limitations": ["No opponent-adjusted or season-separated calibrated model",
                              "No market-implied priors, injuries or roster adjustments",
                              "No probability, fair odds, EV, SGP or Diamond Plays"],
              "evaluations": rows[-2000:]}
    OUTPUT.write_text(json.dumps(output, separators=(",", ":")) + "\n")
    print(json.dumps({k: output[k] for k in ("historical_games", "usable_games", "teams_observed", "walk_forward")}, indent=2))

if __name__ == "__main__":
    main()
