#!/usr/bin/env python3
"""Incremental ESPN men's basketball completed-game cache. No API keys or fabricated rows."""
import datetime as dt
import json
import os
import pathlib
import time
import urllib.parse
import urllib.request

DEST = pathlib.Path("data/ncaab_espn_history.json")
BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/"
HEADERS = {"User-Agent": "KennysSportsLab/1.0 (research cache)", "Accept": "application/json"}

def get(path, params):
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def num(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def extract(summary, event_id, date):
    box = summary.get("boxscore") or {}
    teams = box.get("teams") or []
    if len(teams) != 2:
        return None
    parsed = []
    for item in teams:
        team = item.get("team") or {}
        stats = {}
        for stat in item.get("statistics") or []:
            name = (stat.get("name") or stat.get("label") or "").lower().replace(" ", "")
            stats[name] = stat.get("displayValue", stat.get("value"))
        # ESPN may supply shooting as made-attempted, not separate FGA.
        def attempts(key):
            v = stats.get(key)
            if v is None:
                return None
            if isinstance(v, str) and "-" in v:
                return num(v.split("-")[-1])
            return num(v)
        fga = attempts("fieldgoalsmade-fieldgoalsattempted")
        fta = attempts("freethrowsmade-freethrowsattempted")
        if fga is None:
            fga = num(stats.get("fieldgoalsattempted"))
        if fta is None:
            fta = num(stats.get("freethrowsattempted"))
        orb = num(stats.get("offensiverebounds"))
        tov = num(stats.get("turnovers"))
        possessions = fga - orb + tov + .44 * fta if all(x is not None for x in (fga, orb, tov, fta)) else None
        parsed.append({"id": str(team.get("id") or ""), "name": team.get("displayName"), "homeAway": item.get("homeAway"),
                       "fga": fga, "fta": fta, "orb": orb, "turnovers": tov,
                       "possessions_est": round(possessions, 2) if possessions is not None and possessions > 35 else None})
    competitors = ((summary.get("header") or {}).get("competitions") or [{}])[0].get("competitors") or []
    scores = {str(c.get("id") or (c.get("team") or {}).get("id")): num(c.get("score")) for c in competitors}
    for t in parsed:
        t["points"] = scores.get(t["id"])
    if any(t["points"] is None for t in parsed):
        return None
    return {"event_id": str(event_id), "date": date, "teams": parsed}

def main():
    old = json.loads(DEST.read_text()) if DEST.exists() else {}
    records = {x["event_id"]: x for x in old.get("games", []) if x.get("event_id")}
    today = dt.datetime.now(dt.timezone.utc).date()
    lookback = max(1, min(int(os.getenv("NCAAB_ESPN_LOOKBACK_DAYS", "45")), 730))
    max_new = max(1, min(int(os.getenv("NCAAB_ESPN_MAX_NEW", "300")), 900))
    # Optional historical season sweep, e.g. 2025-01-01 to 2025-04-10.
    start_text = os.getenv("NCAAB_ESPN_START_DATE", "").strip()
    end_text = os.getenv("NCAAB_ESPN_END_DATE", "").strip()
    start = dt.date.fromisoformat(start_text) if start_text else today - dt.timedelta(days=lookback)
    end = dt.date.fromisoformat(end_text) if end_text else today - dt.timedelta(days=1)
    if start > end or (end - start).days > 730 or end >= today:
        raise ValueError("Historical range must be ordered, <=731 days, and before today")
    candidates = []
    errors = []
    seen_candidates = set()
    for offset in range((end - start).days + 1):
        day = start + dt.timedelta(days=offset)
        try:
            board = get("scoreboard", {"dates": day.strftime("%Y%m%d"), "groups": "50", "limit": "500"})
            for event in board.get("events") or []:
                eid = str(event.get("id") or "")
                if eid and eid not in records and eid not in seen_candidates and (event.get("status") or {}).get("type", {}).get("completed") is True:
                    seen_candidates.add(eid)
                    candidates.append((eid, day.isoformat()))
        except Exception as exc:
            errors.append({"day": day.isoformat(), "error": type(exc).__name__})
        time.sleep(0.2)
    # Prioritize newest missing results, then progressively fill older gaps on subsequent runs.
    candidates.sort(key=lambda item: (item[1], item[0]), reverse=True)
    print("Candidate games",len(candidates),"batch budget",max_new)
    added = 0
    for eid, date in candidates[:max_new]:
        try:
            row = extract(get("summary", {"event": eid}), eid, date)
            if row:
                records[eid] = row
                added += 1
        except Exception as exc:
            errors.append({"event_id": eid, "error": type(exc).__name__})
        time.sleep(1.1)
    if errors and not added and not records:
        raise RuntimeError("ESPN fetch failed; preserving previous history")
    if candidates and not added and not errors:
        raise RuntimeError("No candidate boxscores could be parsed; preserving previous history")
    output = {"provider": "espn-public", "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "schema_version": 1, "games": sorted(records.values(), key=lambda r: (r["date"], r["event_id"]))[-12000:],
              "errors": errors[:30]}
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(output, separators=(",", ":")) + "\n")
    print("ESPN games cached", len(output["games"]), "new", added, "errors", len(errors))
    print("games with both teams possessions", sum(all(t.get("possessions_est") is not None for t in g["teams"]) for g in output["games"]))

if __name__ == "__main__":
    main()
