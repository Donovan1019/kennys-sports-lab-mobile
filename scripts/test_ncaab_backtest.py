#!/usr/bin/env python3
"""Deterministic NCAA point-in-time / season-isolation regression checks."""
import importlib.util
spec=importlib.util.spec_from_file_location("audit","scripts/ncaab_research_backtest.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert m.season_key("2025-11-03")==2026
assert m.season_key("2026-03-12")==2026
assert m.season_key("2026-11-03")==2027

def game(day,i,a=80,b=70):
    return {"date":day,"event_id":str(i),"teams":[
        {"id":"1","name":"A","points":a,"possessions_est":70},
        {"id":"2","name":"B","points":b,"possessions_est":70}]}
rows=[]
for i in range(8):
    rows.append(game("2026-03-%02d"%(i+1),i))
# New season begins with no historical prior games; no model evaluation should occur.
rows.append(game("2026-11-03",100))
pred,history=m.evaluate(rows)
assert len(pred)==3, (len(pred),pred)
assert all(x["season"]==2026 for x in pred)
assert len(history["1"])==1 and len(history["2"])==1
summary=m.summarize(pred)
assert summary["games"]==3
assert summary["sample_sufficient"] is False
assert summary["margin_mae"]==0
print("NCAA season-isolation and historical no-leakage tests passed")
