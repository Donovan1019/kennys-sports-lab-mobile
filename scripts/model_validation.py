"""Research-only season breakdown and paired block-bootstrap uncertainty."""
import json
import math
import random
from collections import defaultdict
from pathlib import Path

def _season(date, sport):
    year, month=int(date[:4]),int(date[5:7])
    if sport=="basketball_nba":
        return f"{year if month>=7 else year-1}-{(year+1 if month>=7 else year)%100:02d}"
    return str(year if month>=7 else year-1)

def _loss(model):
    p=model["home_win_probability"]
    y=model["home_won"]
    if type(p) not in (int,float) or not math.isfinite(p) or not 0<=p<=1 or type(y) is not int or y not in (0,1):
        raise ValueError("Invalid scored forecast")
    return (p-y)**2

def summarize(backtest,sport,*,replicates=2000,seed=1729):
    if sport not in ("americanfootball_nfl","basketball_nba"):
        raise ValueError("Unsupported sport")
    if type(replicates) is not int or not 100<=replicates<=10000:
        raise ValueError("Invalid bootstrap size")
    groups=defaultdict(list)
    for row in backtest.get("results",[]):
        try:
            date=row["date"]
            season=_season(date,sport)
            delta=_loss(row["correlated"])-_loss(row["independent"])
            # Weekly blocks for NFL; calendar-month blocks for NBA.
            from datetime import datetime
            dt=datetime.fromisoformat(date.replace("Z","+00:00"))
            block=(dt.strftime("%G-W%V") if sport=="americanfootball_nfl" else dt.strftime("%Y-%m"))
            groups[season].append((block,delta))
        except (KeyError,TypeError,ValueError,OverflowError):
            continue
    per_season=[]
    for season,observations in sorted(groups.items()):
        delta=sum(d for _,d in observations)/len(observations)
        per_season.append({"season":season,"games":len(observations),
                           "correlated_minus_independent_brier":round(delta,6),
                           "winner":"correlated" if delta<0 else "independent" if delta>0 else "tie"})
    all_rows=[item for rows in groups.values() for item in rows]
    if not all_rows:
        return {"status":"awaiting_valid_backtest","sample_size":0,"promotion_approved":False,"seasons":[]}
    blocks=defaultdict(list)
    for season,observations in groups.items():
        for block,delta in observations:
            blocks[(season,block)].append(delta)
    block_values=list(blocks.values())
    rng=random.Random(seed)
    samples=[]
    for _ in range(replicates):
        drawn=[block_values[rng.randrange(len(block_values))] for _ in block_values]
        flat=[v for block in drawn for v in block]
        samples.append(sum(flat)/len(flat))
    samples.sort()
    ci=[round(samples[int(.025*(replicates-1))],6),
        round(samples[int(.975*(replicates-1))],6)]
    overall=sum(d for _,d in all_rows)/len(all_rows)
    return {"status":"research_only","sample_size":len(all_rows),
            "block_count":len(block_values),"bootstrap_replicates":replicates,
            "block_method":"NFL calendar week / NBA calendar month",
            "correlated_minus_independent_brier":round(overall,6),
            "paired_block_bootstrap_95_interval":ci,
            "seasons":per_season,
            "promotion_approved":False,
            "warning":"Block bootstrap is descriptive and does not correct model-selection bias or establish a betting edge. Independent validation is required."}

def main():
    for sport in ("americanfootball_nfl","basketball_nba"):
        source=Path(f"feed/{sport}_correlation_backtest.json")
        if not source.exists():
            print(f"{sport}: no walk-forward backtest")
            continue
        result=summarize(json.loads(source.read_text()),sport)
        Path(f"feed/{sport}_model_validation.json").write_text(json.dumps(result,indent=2)+"\n")
        print(f"{sport}: validation games={result['sample_size']} ci={result.get('paired_block_bootstrap_95_interval')}")
if __name__=="__main__":
    main()
