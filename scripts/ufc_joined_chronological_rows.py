#!/usr/bin/env python3
"""Convert source-native joined UFC fight records into dated fighter exposure rows.

Output is retrospective research only. An observed fight's own statistics must
never enter its pre-fight features; point-in-time provenance remains separate.
"""
import argparse,csv,io,json
from datetime import date
from pathlib import Path
from scripts.ufc_native_fight_join import fetch,join,BASE
from scripts.ufc_historical_prefix_features import build as prefix

def num(raw):
    if raw is None or str(raw).strip()=="" :raise ValueError("missing numeric field")
    n=float(raw)
    if not n.is_integer() or n<0 or n>10000:raise ValueError("invalid count")
    return int(n)
def convert(records):
    rows=[];skipped=[]
    for record in records:
        f=record["wide_record"];fid=record["ufcstats_fight_id"]
        try:
            when=date.fromisoformat(str(f["event_date"])[:10]).isoformat()+"T00:00:00Z"
            duration=num(f["fight_duration_sec"])
            if duration<1 or duration>1500:raise ValueError("invalid duration")
            a=f["f1_id"].strip().lower();b=f["f2_id"].strip().lower()
            if a!=record["fighter_1_ufcstats_id"] or b!=record["fighter_2_ufcstats_id"]:
                raise ValueError("fighter ID mismatch")
            for side,fighter in (("f1",a),("f2",b)):
                sig=num(f[side+"_tot_sig_str_landed"])
                sigatt=num(f[side+"_tot_sig_str_att"])
                td=num(f[side+"_tot_td_landed"])
                tdatt=num(f[side+"_tot_td_att"])
                if sig>sigatt or td>tdatt:raise ValueError("landed > attempted")
                rows.append({"fight_id":fid,"fighter_id":fighter,"fight_time":when,
                    "settled":"true","sig_landed":str(sig),"sig_attempted":str(sigatt),
                    "takedowns_landed":str(td),"takedowns_attempted":str(tdatt),
                    "active_seconds":str(duration)})
        except (ValueError,KeyError,TypeError) as exc:
            skipped.append({"fight_id":fid,"reason":str(exc)})
    return {"source":"nlbair/ufc-data ufc_all_fights_wide.csv",
        "provenance":"RETROSPECTIVE_NOT_PIT_CERTIFIED","bet_eligible":False,
        "total_fights":len(records),"fighter_rows":len(rows),
        "skipped_fights":len(skipped),"skipped_examples":skipped[:30],"rows":rows}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--features-output",type=Path,required=True)
    args=p.parse_args()
    cw,_=fetch(BASE+"id_crosswalk_all.csv")
    wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    joined=join(cw,wide)
    if joined["status"]!="JOINED":raise SystemExit("source ID join failed")
    converted=convert(joined["records"])
    if len(converted["rows"])<5000:raise SystemExit("insufficient fighter rows")
    args.output.write_text(json.dumps(converted,separators=(",",":"))+"\n")
    features=prefix(converted["rows"])
    args.features_output.write_text(json.dumps({"provenance":"RETROSPECTIVE_NOT_PIT_CERTIFIED",
       "bet_eligible":False,"rows":features},separators=(",",":"))+"\n")
    print(json.dumps({k:v for k,v in converted.items() if k!="rows"},indent=2))
    print("Chronological feature rows:",len(features))
if __name__=="__main__":main()
