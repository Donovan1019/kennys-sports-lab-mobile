"""Generate transparent, non-bet-eligible NBA single-leg research candidates.

This does not price same-game parlays, calculate EV, or promote a model.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

MARKETS={"player_points":"Points","player_rebounds":"Rebounds",
         "player_assists":"Assists","player_threes":"Threes"}
ESPN_TEAM_NAMES={
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GS": "Golden State Warriors",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NO": "New Orleans Pelicans",
    "NOP": "New Orleans Pelicans",
    "NY": "New York Knicks",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SA": "San Antonio Spurs",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "UTAH": "Utah Jazz",
    "WAS": "Washington Wizards",
    "WSH": "Washington Wizards"
}

def normalized_team(value):
    team=str(value or "").strip()
    return ESPN_TEAM_NAMES.get(team.upper(),team).casefold()

ROOT=Path(__file__).resolve().parents[1]
FEED=ROOT/"feed"


def stamp(value):
    try:
        dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError, TypeError):
        return None


def generate(odds, history, now):
    output={"schema_version":2,"generated_at":now.isoformat(),
            "model_status":"research_only_not_bet_eligible",
            "prediction_type":"single_leg_empirical_history_not_sgp",
            "predictions":[],"rejections":{}}
    def reject(reason):
        output["rejections"][reason]=output["rejections"].get(reason,0)+1
    if odds.get("sport")!="basketball_nba" or history.get("source")!="espn-public-boxscore" or history.get("sport")!="nba":
        reject("unverified_source");return output
    fetched=stamp(odds.get("fetched_at"))
    if not fetched or not 0<=(now-fetched).total_seconds()<=5400:
        reject("stale_feed");return output
    profiles={str(p.get("name","")).casefold().strip():p for p in history.get("players",[]) if isinstance(p,dict)}
    seen=set()
    for row in odds.get("odds",[]):
        if not isinstance(row,dict):reject("invalid_row");continue
        market=MARKETS.get(row.get("market"))
        if not market:reject("unsupported_market");continue
        quote=stamp(row.get("updated_at"));tip=stamp(row.get("commence_time"))
        if not quote or not tip or not quote<=fetched<=now<tip or (now-quote).total_seconds()>5400:
            reject("quote_timestamp");continue
        key=(row.get("event_id"),row.get("player"),row.get("market"),row.get("selection"),row.get("point"),row.get("bookmaker"))
        if key in seen:continue
        seen.add(key)
        point=row.get("point")
        if type(point) not in (int,float) or row.get("selection") not in ("Over","Under"):
            reject("invalid_line");continue
        profile=profiles.get(str(row.get("player","")).casefold().strip())
        if not profile:reject("player_not_matched");continue
        # A player's historical team must belong to the quoted matchup.
        # Reject ambiguous names, abbreviations and missing team assignments.
        event=row.get("event")
        team=normalized_team(profile.get("team"))
        if not isinstance(event,str) or event.count(" @ ")!=1 or not team:
            reject("unverified_matchup");continue
        away,home=(part.strip().casefold() for part in event.split(" @ "))
        if team not in (away,home):
            reject("player_team_mismatch");continue
        games=[]
        for game in profile.get("games",[]):
            if not isinstance(game,dict):continue
            date=stamp(str(game.get("date",""))+"T00:00:00Z")
            value=(game.get("values") or {}).get(market)
            if date and date<now and type(value) in (int,float) and value>=0:
                games.append((date,value))
        games.sort(key=lambda g:g[0])
        if len(games)<8 or (now-games[-1][0]).days>21:
            reject("insufficient_recent_history");continue
        recent=games[-10:]
        wins=sum((value>point if row["selection"]=="Over" else value<point) for _,value in recent)
        pushes=sum(value==point for _,value in recent)
        output["predictions"].append({
            "event_id":row["event_id"],"event":row.get("event"),"commence_time":row["commence_time"],
            "player":row["player"],"market":row["market"],"selection":row["selection"],
            "point":point,"bookmaker":row.get("bookmaker"),"price":row.get("price"),
            "quote_updated_at":row["updated_at"],"sample_size":len(recent),
            "historical_hits":wins,"historical_pushes":pushes,
            "historical_hit_rate":round(wins/len(recent),4),
            "model_probability":None,"ev":None,"sgp_joint_probability":None,
            "research_only":True,"bet_eligible":False,
            "warning":"Retrospective hit rate at current line, not calibrated or point-in-time validated. No injury/lineup verification."})
    output["predictions"].sort(key=lambda p:(-p["historical_hit_rate"],-p["sample_size"],p["player"]))
    return output


def run():
    now=datetime.now(timezone.utc)
    try:
        odds=json.loads((FEED/"nba_props.json").read_text())
        history=json.loads((FEED/"nba_player_stats.json").read_text())
    except (OSError, ValueError) as exc:
        result={"schema_version":2,"generated_at":now.isoformat(),"model_status":"research_only_source_unavailable","predictions":[],"error":type(exc).__name__}
    else:
        result=generate(odds,history,now)
    (FEED/"nba_model_candidates.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"model_status":result["model_status"],"candidate_count":len(result["predictions"]),"rejections":result.get("rejections",{})}))
    return result


if __name__=="__main__":
    run()
