"""Bridge actual independently saved NBA SGP model recommendations to grading ledger.

No synthetic picks, bookmaker prices, or model probabilities are generated.
"""
import json
from pathlib import Path
from datetime import datetime,timezone
import math
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
            if row.get("model_probability") is None or not isinstance(row.get("model_probability"),(int,float)) or isinstance(row.get("model_probability"),bool) or not 0<row["model_probability"]<1:
                raise ValueError("missing calibrated joint model probability")
            if not math.isfinite(row["model_probability"]):
                raise ValueError("non-finite joint probability")
            if not row.get("joint_simulation_id") or not row.get("correlation_model_version"):
                raise ValueError("missing joint simulation or correlation provenance")
            if row.get("simulation_validated") is not True:
                raise ValueError("joint simulation not validated")
            if not row.get("model_version") or not row.get("model_source"):
                raise ValueError("missing model provenance")
            captured_at=stamp(row.get("captured_at"))
            if not captured_at or captured_at>now:
                raise ValueError("future or missing capture time")
            tip=stamp(row.get("commence_time"))
            if not tip or captured_at>=tip:
                raise ValueError("model recommendation is not pregame")
            model_at=stamp(row.get("model_generated_at"))
            if not model_at or model_at>captured_at or model_at>=tip:
                raise ValueError("missing or invalid point-in-time model generation timestamp")
            if (captured_at-model_at).total_seconds()>5400:
                raise ValueError("model recommendation older than 90 minutes")
            if not row.get("sgp_bookmaker_quote") or not isinstance(row.get("sgp_bookmaker_quote"),dict):
                raise ValueError("missing actual bookmaker same-game parlay price")
            sgp_quote=row["sgp_bookmaker_quote"]
            if not sgp_quote.get("bookmaker") or not isinstance(sgp_quote.get("price"),(int,float)) or isinstance(sgp_quote.get("price"),bool):
                raise ValueError("invalid bookmaker SGP price")
            quote_at=stamp(sgp_quote.get("updated_at"))
            if not quote_at or quote_at>captured_at or quote_at>=tip or (captured_at-quote_at).total_seconds()>5400:
                raise ValueError("SGP quote timestamp unverified")
            if not row.get("legs") or any(not isinstance(leg,dict) or not isinstance(leg.get("price"),(int,float)) or isinstance(leg.get("price"),bool) or not math.isfinite(leg.get("price")) or not leg.get("bookmaker") or not stamp(leg.get("updated_at")) or (captured_at-stamp(leg.get("updated_at"))).total_seconds()>5400 for leg in row["legs"]):
                raise ValueError("missing actual sportsbook leg prices")
            if not math.isfinite(sgp_quote["price"]) or sgp_quote["price"]==0 or -100<sgp_quote["price"]<100:
                raise ValueError("invalid American SGP quote")
            if any(stamp(leg["updated_at"])>captured_at or stamp(leg["updated_at"])>=tip for leg in row["legs"]):
                raise ValueError("leg quote is future-dated or post-tipoff")
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
