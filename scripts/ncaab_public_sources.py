#!/usr/bin/env python3
"""Audit public NCAA basketball data sources without keys or scraping protected sites."""
import datetime as dt
import json
import os
import pathlib
import urllib.request

DEST = pathlib.Path("data/ncaab_public_sources.json")
URL = "https://api.github.com/repos/sportsdataverse/hoopR-mbb-data/releases?per_page=100"
WANTED = {
    "espn_mens_college_basketball_team_boxscores",
    "espn_mens_college_basketball_player_boxscores",
    "espn_mens_college_basketball_schedules",
    "espn_mens_college_basketball_pbp",
    "espn_mens_college_basketball_rosters",
    "mbb_crosswalk",
}
def audit():
    req = urllib.request.Request(URL, headers={"Accept":"application/vnd.github+json","User-Agent":"KennysSportsLab-public-data-audit"})
    with urllib.request.urlopen(req, timeout=25) as response:
        releases = json.load(response)
    if not isinstance(releases, list):
        raise ValueError("Unexpected GitHub release metadata")
    found = {}
    for release in releases:
        tag = release.get("tag_name", "")
        if tag not in WANTED:
            continue
        assets = []
        for asset in release.get("assets") or []:
            url = asset.get("browser_download_url", "")
            if not url.startswith("https://github.com/sportsdataverse/hoopR-mbb-data/releases/download/"):
                continue
            assets.append({"name":asset.get("name"),"size_bytes":asset.get("size"),"updated_at":asset.get("updated_at"),"url":url})
        found[tag] = {"release_url":release.get("html_url"),"published_at":release.get("published_at"),"assets":assets}
    if not found:
        raise RuntimeError("No supported public release datasets discovered")
    return {"provider":"sportsdataverse-hoopr-public-releases","checked_at":dt.datetime.now(dt.timezone.utc).isoformat(),"source_url":URL,"datasets":found,"status":"METADATA_ONLY","limitations":["Availability audit only; no unverified game rows or model predictions imported","Bulk ingestion requires explicit schema and historical identity checks","Do not fetch subscription-only or access-controlled sources"]}
def main():
    result = audit()
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("Public NCAA datasets:",len(result["datasets"]),"assets:",sum(len(v["assets"]) for v in result["datasets"].values()))
if __name__ == "__main__":
    main()
