#!/usr/bin/env node
'use strict';
// Independent event-level audit of archived NFL model forecasts versus pregame market consensus.
// One earliest forecast per event, exact forecast-id join, no future quotes, no duplicated events.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),read=n=>JSON.parse(fs.readFileSync(path.join(root,'feed',n),'utf8'));
const forecasts=read('americanfootball_nfl_forecast_ledger.json').forecasts;
const baselines=read('americanfootball_nfl_market_baseline_ledger.json').baselines;
const outcomes=read('americanfootball_nfl_forecast_outcomes.json').scored;
const byBaseline=new Map(baselines.map(x=>[x.forecast_id,x]));
const byOutcome=new Map();const conflictingOutcomes=new Set();for(const x of outcomes){if(!x.forecast_id)continue;const old=byOutcome.get(x.forecast_id);if(old&&old.home_won!==x.home_won)conflictingOutcomes.add(x.forecast_id);else if(!old)byOutcome.set(x.forecast_id,x)}
const earliest=new Map(),rejected={};
const reject=reason=>{rejected[reason]=(rejected[reason]||0)+1};
for(const f of forecasts){
 const t=Date.parse(f.forecast_at),start=Date.parse(f.event_start);
 if(!f.event_id||!f.forecast_id||!Number.isFinite(t)||!Number.isFinite(start)||t>=start||!(f.home_probability>0&&f.home_probability<1)){reject('invalid_forecast');continue}
 const prior=earliest.get(f.event_id);if(!prior||t<Date.parse(prior.forecast_at))earliest.set(f.event_id,f);
}
const rows=[];
for(const f of earliest.values()){
 const b=byBaseline.get(f.forecast_id),o=byOutcome.get(f.forecast_id);
 if(!b){reject('no_matching_market_baseline');continue}
 if(b.event_id!==f.event_id||b.forecast_at!==f.forecast_at||b.event_start!==f.event_start||b.status!=='verified_pregame_quote'||b.source!=='multi_book_no_vig_consensus'||!Number.isFinite(Date.parse(b.quote_at))||Date.parse(b.quote_at)>Date.parse(f.forecast_at)||Date.parse(b.quote_at)>=Date.parse(f.event_start)||!(b.home_probability>0&&b.home_probability<1)){reject('invalid_or_future_market_quote');continue}
 if(conflictingOutcomes.has(f.forecast_id)){reject('conflicting_outcomes');continue}
 if(!o||!(o.home_won===0||o.home_won===1)){reject('no_verified_outcome');continue}
 const y=o.home_won;rows.push({event_id:f.event_id,model_brier:(f.home_probability-y)**2,market_brier:(b.home_probability-y)**2,model_probability:f.home_probability,market_probability:b.home_probability});
}
const mean=k=>rows.reduce((s,x)=>s+x[k],0)/rows.length;
const scoredEventIds=new Set(rows.map(x=>x.event_id));
const ungradedEvents=[...earliest.keys()].filter(id=>!scoredEventIds.has(id));
const minimum=100,report={status:'RESEARCH_ONLY_NOT_BET_ELIGIBLE',archived_events:earliest.size,scored_events:rows.length,ungraded_unique_events:ungradedEvents.length,minimum_sample:minimum,rejected,model_brier:rows.length?mean('model_brier'):null,market_brier:rows.length?mean('market_brier'):null,market_relative_brier_skill:rows.length>=minimum&&mean('market_brier')>0?1-mean('model_brier')/mean('market_brier'):null,exploratory_market_relative_brier_skill:rows.length&&mean('market_brier')>0?1-mean('model_brier')/mean('market_brier'):null,market_outperformance_established:false,betting_ready:false,readiness_reason:rows.length<minimum?'Insufficient independently graded, event-deduplicated forecasts versus pregame market baseline':'Independent holdout and executable-price validation remain required',notes:['One earliest forecast per event and exact forecast ID matching','Quote must predate forecast and kickoff','Independent holdout, sufficient event counts and timestamped executable odds required for betting approval','Archived forecasts and outcomes remain research-only']};
const output=path.join(root,'reports','nfl_market_accuracy.json');
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify({...report,generated_at:new Date().toISOString(),scope:'NFL game moneyline only; player props, spreads and totals are not evaluated by this report'},null,2)+'\n');
console.log(JSON.stringify(report,null,2));
