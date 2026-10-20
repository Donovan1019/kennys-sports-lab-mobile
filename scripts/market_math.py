"""Pure, dependency-free odds research utilities.

These functions operate only on verified market prices; they do NOT create a
sports outcome projection. Never call market consensus a calibrated model.
"""
from collections import defaultdict
from math import isfinite

def implied_probability(american):
    price=float(american)
    if not isfinite(price) or (-100 < price < 100):
        raise ValueError("Invalid American odds")
    return -price/(100-price) if price < 0 else 100/(100+price)

def net_profit_per_unit(american):
    price=float(american)
    implied_probability(price)
    return 100/(-price) if price < 0 else price/100

def expected_value(american, estimated_probability):
    p=float(estimated_probability)
    if not isfinite(p) or not 0 <= p <= 1:
        raise ValueError("Probability must be between 0 and 1")
    return p*net_profit_per_unit(american)-(1-p)

def paired_two_way_no_vig(first, second):
    p1,p2=implied_probability(first),implied_probability(second)
    return p1/(p1+p2),p2/(p1+p2)

def best_prices(rows):
    """Compare identical event/market/selection/point/description across books."""
    groups=defaultdict(list)
    for row in rows:
        key=(row.get("event_id"),row.get("market"),row.get("selection"),row.get("point"),row.get("description"))
        try:
            net_profit_per_unit(row["price"])
        except (KeyError, ValueError, TypeError):
            continue
        groups[key].append(row)
    return {key:max(group,key=lambda x:net_profit_per_unit(x["price"])) for key,group in groups.items()}

def fair_american(probability):
    p=float(probability)
    if not isfinite(p) or not 0 < p < 1:
        raise ValueError("Probability must be strictly between 0 and 1")
    return round(-100*p/(1-p) if p >= .5 else 100*(1-p)/p)
