"""Bridge actual independently saved NBA SGP model recommendations to grading ledger.

No synthetic picks, bookmaker prices, or model probabilities are generated.
"""
import json
from pathlib import Path
from datetime import datetime,timezone
from scripts.ingest_nba_sgp_snapshot import ingest,stamp,LEDGER

SOURCE=Path("feed/nba_sgp_model_recommendations.json")
REPORT=Path("feed/nba_sgp_model_capture_status.json")

def run():
    now=datetime.now(timezone.utc)
    try: data=json.loads(SOURCE.read_text())
    except (OSError,ValueError): data={}
    records=data.get("recommendations",[]) if isinstance(data,dict) else []
    if not isinstance(records,list): records=[]
    existing=set()
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            try: existing.add(str(json.loads(line).get("sgp_id")))
            except (ValueError,TypeError,AttributeError): pass
    captured=0;rejected=[]
    for row in records:
        if not isinstance(row,dict):
            rejected.append("invalid recommendation record");continue
        sid=str(row.get("sgp_id") or "")
        if sid in existing: continue
        try:
            if row.get("model_recommendation") is not True:
                raise ValueError("not an independently recorded model recommendation")
            if row.get("research_only") is not True or row.get("bet_eligible") is True:
                raise ValueError("research-only recommendation required")
            if not row.get("model_version") or not row.get("model_source"):
                raise ValueError("missing model provenance")
            captured_at=stamp(row.get("captured_at"))
            if not captured_at or captured_at>now:
                raise ValueError("future or missing capture time")
            if not row.get("legs") or any(not isinstance(leg,dict) or not leg.get("price") or not leg.get("bookmaker") for leg in row["legs"]):
                raise ValueError("missing actual sportsbook leg prices")
            ingest(row)
            existing.add(sid);captured+=1
        except (ValueError,TypeError,KeyError) as exc:
            rejected.append(sid+": "+str(exc))
    report={"checked_at":now.isoformat(),"source_present":SOURCE.exists(),
            "source_recommendations":len(records),"captured":captured,"rejected":rejected,
            "status":"CAPTURED" if captured else "NO_NEW_VERIFIED_MODEL_RECOMMENDATIONS",
            "note":"Only genuine source-recorded recommendations are archived; none are invented."}
    REPORT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
    return report

if __name__=="__main__":run()
