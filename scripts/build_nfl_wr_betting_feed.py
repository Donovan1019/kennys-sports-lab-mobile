"""Join existing NFL prop quotes to independently verified model predictions; fail closed."""
import json
from pathlib import Path
from scripts.validate_nfl_wr_betting import process

ODDS = Path("feed/nfl_wr_prop_odds.json")
PREDICTIONS = Path("data/nfl_wr_betting_input.json")
OUTPUT = Path("feed/nfl_wr_betting.json")
MARKETS = {"player_receptions":"receptions","player_reception_yds":"receiving_yards","player_anytime_td":"receiving_touchdowns"}

def join(odds, predictions):
    candidates = []
    index = {}
    for p in predictions.get("picks", []):
        key = (p.get("event_id"),p.get("player_name"),p.get("market"),p.get("side"),p.get("line"))
        if all(v is not None for v in key):
            if key in index:
                index[key] = None  # ambiguous projections must never match
            else:
                index[key] = p
    for quote in odds.get("odds", []):
        market = MARKETS.get(quote.get("market"))
        side = str(quote.get("side","")).lower()
        if market == "receiving_touchdowns" and side == "yes":
            side = "over"
        key = (quote.get("event_id"),quote.get("player_name"),market,side,quote.get("line"))
        p = index.get(key)
        if not p:
            continue
        candidate = dict(p)
        candidate.update({k:quote[k] for k in ("player_name","line","american_odds","book","verified_at","event_id")})
        candidate["market"] = market
        candidate["side"] = side
        candidates.append(candidate)
    return candidates

def main():
    if not ODDS.exists() or not PREDICTIONS.exists():
        result = process({"picks":[]})
    else:
        result = process({"picks":join(json.loads(ODDS.read_text()),json.loads(PREDICTIONS.read_text()))})
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2)+"\n")
    print("Validated",len(result["picks"]),"exact-match WR betting candidates")

if __name__ == "__main__":
    main()
