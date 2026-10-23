#!/usr/bin/env python3
"""UFC moneyline market mathematics and fail-closed research candidate grading.

All inputs must be independently verified and model calibration approved before
a recommendation can be considered eligible. This module never fetches odds.
"""
import datetime as dt
import math

def decimal_odds(american):
    if type(american) not in (int,float) or not math.isfinite(american) or -100<american<100:
        raise ValueError("Invalid American odds")
    return 1+american/100 if american>0 else 1+100/abs(american)

def implied(american):
    return 1/decimal_odds(american)

def no_vig_pair(a,b):
    x,y=implied(a),implied(b)
    if x+y<0.95 or x+y>1.35:
        raise ValueError("Suspicious two-way book sum")
    return x/(x+y),y/(x+y)

def assess(quote):
    required=("event_id","fighter","opponent","fighter_odds","opponent_odds",
              "observed_at_utc","event_start_utc","sportsbook",
              "model_probability","model_calibrated","fighters_verified",
              "source_verified","odds_executable")
    missing=[k for k in required if k not in quote]
    if missing:
        return {"eligible":False,"reason":"MISSING_FIELDS","missing":missing}
    try:
        prob=quote["model_probability"]
        if type(prob) not in (float,int) or not math.isfinite(prob) or not 0<prob<1:
            raise ValueError("Invalid probability")
        obs=dt.datetime.fromisoformat(quote["observed_at_utc"].replace("Z","+00:00"))
        event=dt.datetime.fromisoformat(quote["event_start_utc"].replace("Z","+00:00"))
        if obs.utcoffset() is None or event.utcoffset() is None or not obs<event:
            raise ValueError("Unverified timestamp ordering")
        if not all(isinstance(quote[k],str) and quote[k].strip() for k in ("event_id","fighter","opponent","sportsbook")):
            raise ValueError("Missing identity")
        if quote["fighter"]==quote["opponent"]:
            raise ValueError("Identical fighters")
        market,other=no_vig_pair(quote["fighter_odds"],quote["opponent_odds"])
        dec=decimal_odds(quote["fighter_odds"])
    except (ValueError,TypeError,AttributeError,OverflowError) as exc:
        return {"eligible":False,"reason":"INVALID_INPUT","detail":str(exc)}
    ev=prob*(dec-1)-(1-prob)
    out={"eligible":False,"event_id":quote["event_id"],"sportsbook":quote["sportsbook"],
         "fighter":quote["fighter"],"opponent":quote["opponent"],
         "model_probability":prob,"market_implied_probability":implied(quote["fighter_odds"]),
         "no_vig_market_probability":market,"no_vig_opponent_probability":other,
         "fair_american_odds":(-100*prob/(1-prob) if prob>=0.5 else 100*(1-prob)/prob),
         "model_edge":prob-market,"expected_roi_per_unit":ev,
         "break_even_probability":1/dec,"kelly_fraction_raw":max(0,(prob*dec-1)/(dec-1)),
         "stake_fraction_recommended":0.0}
    flags=("model_calibrated","fighters_verified","source_verified","odds_executable")
    if any(quote[k] is not True for k in flags):
        out["reason"]="VERIFICATION_OR_CALIBRATION_INCOMPLETE"
    elif ev<=0:
        out["reason"]="NONPOSITIVE_EV"
    else:
        out["eligible"]=True
        out["reason"]="VERIFIED_POSITIVE_EV_CANDIDATE_REQUIRES_RISK_REVIEW"
    return out
