#!/usr/bin/env node
// Validate a foundation-produced, timestamped NFL prediction export before
// exposing it to the mobile calibration audit. Does not invent predictions.
'use strict';
const fs=require('node:fs');
const source=process.argv[2],dest=process.argv[3];
if(!source||!dest){console.error('Usage: node scripts/bridge_nfl_research.cjs archived-predictions.json mobile-audit-input.json');process.exit(2)}
let rows;try{rows=JSON.parse(fs.readFileSync(source,'utf8'))}catch(e){console.error('Invalid research export: '+e.message);process.exit(2)}
if(!Array.isArray(rows)||!rows.length){console.error('No archived research predictions');process.exit(2)}
const required=['market','event_id','kickoff','quoted_at','forecast_at','graded_at','player','line','over_odds','under_odds','model_probability','outcome'];
const errors=[];
for(let i=0;i<rows.length;i++){
 const r=rows[i];
 for(const k of required)if(r[k]===undefined||r[k]===null||r[k]==='')errors.push('row '+i+' missing '+k);
 if(!r.source_repository||!r.source_commit||!r.forecast_id)errors.push('row '+i+' missing foundation provenance');
 if(!Number.isFinite(Date.parse(r.forecast_at))||!Number.isFinite(Date.parse(r.kickoff))||Date.parse(r.forecast_at)>=Date.parse(r.kickoff))errors.push('row '+i+' invalid pregame forecast');
 if(!Number.isFinite(Date.parse(r.quoted_at))||Date.parse(r.quoted_at)>Date.parse(r.forecast_at)||Date.parse(r.quoted_at)>=Date.parse(r.kickoff))errors.push('row '+i+' invalid or future sportsbook quote');
 if(!Number.isFinite(Date.parse(r.graded_at))||Date.parse(r.graded_at)<Date.parse(r.kickoff))errors.push('row '+i+' outcome graded before kickoff');
 if(r.source_repository!=='Donovan1019/sports-model-foundation')errors.push('row '+i+' unknown source');
}
if(errors.length){console.error(JSON.stringify({status:'REJECTED',errors:errors.slice(0,30),count:errors.length},null,2));process.exit(1)}
fs.writeFileSync(dest,JSON.stringify(rows,null,2)+'\n');
console.log(JSON.stringify({status:'ARCHIVED_RESEARCH_EXPORT_VALIDATED',rows:rows.length,output:dest,betting_ready:false}));
