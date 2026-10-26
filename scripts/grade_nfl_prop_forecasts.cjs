#!/usr/bin/env node
'use strict';
// Grade immutable pregame predictions ONLY against independently supplied exact-event player outcomes.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const ledgerPath=path.join(root,'feed','nfl_prop_forecast_ledger.json');
const outcomesPath=process.argv[2]||path.join(root,'feed','nfl_prop_verified_outcomes.json');
const output=path.join(root,'feed','nfl_prop_graded_snapshots.json');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
if(!fs.existsSync(ledgerPath)||!fs.existsSync(outcomesPath)){
 console.log(JSON.stringify({status:'AWAITING_VERIFIED_INPUTS',ledger:fs.existsSync(ledgerPath),outcomes:fs.existsSync(outcomesPath),betting_ready:false}));process.exit(0);
}
const forecasts=read(ledgerPath).forecasts,outcomes=read(outcomesPath);
const sourceAllowed=s=>typeof s==='string'&&/^https:\/\//.test(s);
if(!Array.isArray(forecasts)||!Array.isArray(outcomes)){console.error('Invalid archive or outcome format');process.exit(1)}
const index=new Map(),conflicts=new Set();
for(const o of outcomes){
 if(!o.event_id||!o.player||!o.market||!Number.isFinite(o.outcome)||!sourceAllowed(o.source)||!o.verified_at||!Number.isFinite(Date.parse(o.verified_at))){console.error('Unverified outcome row');process.exit(1)}
 const key=[o.event_id,o.player,o.market].join('|'),old=index.get(key);
 if(old&&JSON.stringify(old)!==JSON.stringify(o))conflicts.add(key);
 else if(!old)index.set(key,o);
}
const graded=[];let unmatched=0;
for(const f of forecasts){
 const key=[f.event_id,f.player,f.market].join('|');
 if(conflicts.has(key)){console.error('Conflicting outcome for '+key);process.exit(1)}
 const o=index.get(key);
 if(!o||o.outcome_verified!==true||!o.espn_event_id||!o.event){unmatched++;continue}
 if(Date.parse(o.verified_at)<Date.parse(f.kickoff)){console.error('Outcome verified before kickoff '+key);process.exit(1)}
 graded.push({...f,graded_at:o.verified_at,outcome:o.outcome,event:o.event,espn_event_id:o.espn_event_id,outcome_verified:true,source:o.source});
}
// Rebuild graded archive only from freshly reconciled independent results.\nfs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(graded,null,2)+'\n');
console.log(JSON.stringify({status:'RESEARCH_ONLY',newly_matched:graded.length,unmatched,graded_total:graded.length,betting_ready:false}));
