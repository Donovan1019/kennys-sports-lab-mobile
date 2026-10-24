"""Opponent defense and recent-form UFC features built only from prior bouts.

All fight statistics are post-fight observations and are incorporated only
after the event date. Research only: retrospective source not PIT certified.
"""
from collections import defaultdict
from datetime import date
def n(x):
    try:return float(x)
    except (TypeError,ValueError):return None
def prior_defense(records):
    bouts=defaultdict(list)
    for rec in records:
        f=rec["wide_record"]
        try:
            day=date.fromisoformat(str(f["event_date"])[:10]).isoformat()
            seconds=n(f["fight_duration_sec"])
            if seconds is None or seconds<=0:continue
            a=rec["fighter_1_ufcstats_id"];b=rec["fighter_2_ufcstats_id"]
            values={}
            for side in ("f1","f2"):
                sig=n(f[side+"_tot_sig_str_landed"])
                td=n(f[side+"_tot_td_landed"])
                if sig is None or td is None or min(sig,td)<0:raise ValueError("missing counts")
                values[side]=(sig,td)
            bouts[day].append((rec["ufcstats_fight_id"],a,b,seconds,values))
        except (KeyError,ValueError,TypeError):continue
    history=defaultdict(list);out={}
    for day in sorted(bouts):
        # Compute every fight on an event date before updating any fighter.
        for fid,a,b,seconds,v in bouts[day]:
            features={}
            for fighter in (a,b):
                prior=history[fighter]
                exposure=sum(x[0] for x in prior)
                recent=prior[-3:]
                recent_exposure=sum(x[0] for x in recent)
                features[fighter]={
                  "prior_defense_fights":len(prior),
                  "sig_absorbed_per_min":sum(x[1] for x in prior)*60/exposure if exposure else None,
                  "td_conceded_per_15min":sum(x[2] for x in prior)*900/exposure if exposure else None,
                  "recent3_sig_absorbed_per_min":sum(x[1] for x in recent)*60/recent_exposure if recent_exposure else None,
                  "recent3_td_conceded_per_15min":sum(x[2] for x in recent)*900/recent_exposure if recent_exposure else None}
            out[(fid,a)]=features[a];out[(fid,b)]=features[b]
        for fid,a,b,seconds,v in bouts[day]:
            history[a].append((seconds,v["f2"][0],v["f2"][1]))
            history[b].append((seconds,v["f1"][0],v["f1"][1]))
    return out
def enrich(rows,records):
    defense=prior_defense(records)
    out=[];missing=0
    lookup={r["ufcstats_fight_id"]:r for r in records}
    for row in rows:
        rec=lookup.get(row["fight_id"])
        if not rec:missing+=1;continue
        a=defense.get((row["fight_id"],rec["fighter_1_ufcstats_id"]))
        b=defense.get((row["fight_id"],rec["fighter_2_ufcstats_id"]))
        if not a or not b or min(a["prior_defense_fights"],b["prior_defense_fights"])<2:
            missing+=1;continue
        fields=("sig_absorbed_per_min","td_conceded_per_15min",
                "recent3_sig_absorbed_per_min","recent3_td_conceded_per_15min")
        if any(a[k] is None or b[k] is None for k in fields):missing+=1;continue
        x=[max(-3,min(3,(a[k]-b[k])/scale)) for k,scale in zip(fields,(4,3,4,3))]
        import hashlib
        if int(hashlib.sha256(row["fight_id"].encode()).hexdigest(),16)%2:x=[-v for v in x]
        out.append({**row,"x":row["x"]+x})
    return out,missing
