#!/usr/bin/env python3
"""Probe the official NFL injury page; never infer player statuses from page text."""
import json
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

URL="https://www.nfl.com/injuries/"
DEST=Path("feed/nfl_injury_source_health.json")

def main():
    now=datetime.now(timezone.utc).isoformat()
    record={"source_url":URL,"checked_at":now,"verified_player_reports":0,"ingestion_status":"UNAVAILABLE","reason":"No validated official player-level parser configured"}
    try:
        request=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 KennySportsLab-InjurySourceCheck/1.0","Accept":"text/html"})
        with urllib.request.urlopen(request,timeout=20) as response:
            content_type=response.headers.get("Content-Type","")
            payload=response.read(2_000_001)
            if len(payload)>2_000_000:raise ValueError("Oversized response")
            if "html" not in content_type.lower():raise ValueError("Unexpected content type")
            if not payload.strip():raise ValueError("Empty response")
            record["source_reachable"]=True
            record["ingestion_status"]="SOURCE_REACHABLE_PARSER_UNAVAILABLE"
    except Exception as error:
        record["source_reachable"]=False
        record["reason"]="Source check failed: "+type(error).__name__
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(record["ingestion_status"])
if __name__=="__main__":main()
