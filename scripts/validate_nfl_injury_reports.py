#!/usr/bin/env python3
"""Validate externally supplied NFL player report snapshot without inventing entries."""
import json,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse

ALLOWED={"nfl.com","www.nfl.com","espn.com","www.espn.com"}
STATUS={"game_designation":{"out","doubtful","questionable"},"official_inactives":{"active","inactive"}}
def parse_time(value):
    if not isinstance(value,str):raise ValueError("timestamp missing")
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("timezone required")
    return t
def validate(data,now=None):
    now=now or datetime.now(timezone.utc)
    if not isinstance(data,dict) or not isinstance(data.get("reports"),list):raise ValueError("reports array required")
    if not data["reports"]:raise ValueError("No verified reports to publish")
    for report in data["reports"]:
        if not isinstance(report,dict) or report.get("verified") is not True:raise ValueError("Unverified report")
        kind=report.get("report_type")
        if kind not in STATUS:raise ValueError("Invalid report type")
        if not isinstance(report.get("event_id"),str) or not report["event_id"].strip():raise ValueError("Event id required")
        parsed=urlparse(str(report.get("source_url","")))
        if parsed.scheme!="https" or parsed.hostname not in ALLOWED or parsed.username or parsed.password:raise ValueError("Untrusted source")
        fetched=parse_time(report.get("fetched_at"))
        if fetched>now or (now-fetched).total_seconds()>=21600:raise ValueError("Stale source")
        players=report.get("players")
        if not isinstance(players,list) or not players:raise ValueError("Empty report")
        for player in players:
            if not isinstance(player,dict) or not all(isinstance(player.get(k),str) and player[k].strip() for k in ("name","team")):raise ValueError("Missing player identity")
            if player.get("status") not in STATUS[kind]:raise ValueError("Wrong status for report type")
    return len(data["reports"])
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: validate_nfl_injury_reports.py PATH")
    count=validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    print("Validated",count,"source-backed injury reports")
