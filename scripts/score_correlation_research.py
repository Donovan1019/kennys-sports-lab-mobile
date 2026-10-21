"""Strictly historical team-score correlation research, never future-data fitted."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

def _date(row):
    try:
        dt=datetime.fromisoformat(row["date"].replace("Z","+00:00"))
        return dt if dt.tzinfo else None
    except (KeyError,TypeError,AttributeError,ValueError):
        return None

def estimate(games, cutoff, *, minimum=40, shrinkage=40):
    """Estimate cross-team score correlation from games strictly before cutoff.

    Scores are centered within each game by their historical sample means.
    Shrink toward zero to reduce overfitting; observational, not causal.
    """
    if cutoff.tzinfo is None:
        raise ValueError("Timezone-aware cutoff required")
    if type(minimum) is not int or minimum < 3 or type(shrinkage) not in (int,float) or shrinkage < 0 or not math.isfinite(shrinkage):
        raise ValueError("Invalid estimator configuration")
    rows=[]
    seen=set()
    for g in games:
        date=_date(g)
        a,h=g.get("away_score"),g.get("home_score")
        key=g.get("event_id") or (g.get("date"),g.get("away"),g.get("home"))
        if key in seen or not date or date>=cutoff or type(a) not in (int,float) or type(h) not in (int,float) or not math.isfinite(a) or not math.isfinite(h) or min(a,h)<0:
            continue
        seen.add(key)
        rows.append((a,h))
    n=len(rows)
    if n<minimum:
        return {"status":"insufficient_history","sample_size":n,"correlation":None}
    am=sum(a for a,_ in rows)/n
    hm=sum(h for _,h in rows)/n
    cov=sum((a-am)*(h-hm) for a,h in rows)
    av=sum((a-am)**2 for a,_ in rows)
    hv=sum((h-hm)**2 for _,h in rows)
    if av<=0 or hv<=0:
        return {"status":"zero_variance","sample_size":n,"correlation":None}
    raw=max(-1,min(1,cov/math.sqrt(av*hv)))
    value=max(-.95,min(.95,raw*n/(n+shrinkage)))
    return {"status":"experimental_historical_estimate","sample_size":n,
            "raw_correlation":round(raw,6),"correlation":round(value,6),
            "cutoff_exclusive":cutoff.isoformat(),
            "warning":"Unadjusted historical score correlation; not validated as a predictive or SGP parameter."}

def main():
    for sport,league in (("americanfootball_nfl","nfl"),("basketball_nba","nba")):
        path=Path(f"feed/{league}_completed_games.json")
        if not path.exists():
            print(f"{sport}: historical correlation unavailable")
            continue
        data=json.loads(path.read_text())
        cutoff=datetime.now(timezone.utc)
        result=estimate(data.get("games",[]),cutoff)
        Path(f"feed/{sport}_score_correlation_research.json").write_text(json.dumps(result,indent=2)+"\n")
        print(f"{sport}: score correlation research {result['status']} n={result['sample_size']}")
if __name__=="__main__":
    main()
