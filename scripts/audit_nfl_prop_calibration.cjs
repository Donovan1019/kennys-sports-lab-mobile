#!/usr/bin/env node
// Historical, chronological, no-lookahead NFL player prop audit.
// Usage: node scripts/audit_nfl_prop_calibration.cjs path/to/graded_snapshots.json
// Input array rows: {market,event_id,kickoff,quoted_at,forecast_at,graded_at,player,line,
// over_odds,under_odds,model_probability,outcome,selection?,bet_odds?}
// model_probability MUST be archived before kickoff; never reconstruct from final stats.
'use strict';
const fs=require('node:fs');
const assert=require('node:assert/strict');
const input=process.argv[2];
if(!input){console.error('UNVERIFIED: provide archived, timestamped graded snapshots JSON');process.exit(2)}
let rows;try{rows=JSON.parse(fs.readFileSync(input,'utf8'))}catch(e){console.error('UNVERIFIED: cannot parse input: '+e.message);process.exit(2)}
if(!Array.isArray(rows)||!rows.length){console.error('UNVERIFIED: no graded snapshots');process.exit(2)}
const date=x=>Date.parse(x),validDate=x=>Number.isFinite(date(x));
const implied=o=>o>0?100/(o+100):-o/(-o+100);
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const market={};
const errors=[];const seen=new Set();
for(const [i,r] of rows.entries()){
 const key=[r.event_id,r.player,r.market,r.line,r.quoted_at].join('|');
 if(seen.has(key)){errors.push('duplicate snapshot '+i);continue}seen.add(key);
 if(!r.market||!r.event_id||!r.player||![r.kickoff,r.quoted_at,r.forecast_at,r.graded_at].every(validDate)||date(r.quoted_at)>=date(r.kickoff)||date(r.forecast_at)>=date(r.kickoff)||date(r.quoted_at)>date(r.forecast_at)||date(r.graded_at)<date(r.kickoff)){errors.push('invalid timing/identity '+i);continue}
 if(![r.line,r.outcome,r.model_probability,r.over_odds,r.under_odds].every(Number.isFinite)||r.model_probability<=0||r.model_probability>=1||r.over_odds===0||r.under_odds===0){errors.push('invalid numeric fields '+i);continue}
 if(r.outcome===r.line)continue; // pushes are neither wins nor losses
 const po=implied(r.over_odds),pu=implied(r.under_odds);
 if(!(po>0&&po<1&&pu>0&&pu<1)){errors.push('invalid prices '+i);continue}
 const p0=po/(po+pu),p=r.model_probability,y=Number(r.outcome>r.line);
 (market[r.market]??=[]).push({p,p0,y,r});
}
if(errors.length){console.error(JSON.stringify({status:'FAIL_DATA_INTEGRITY',errors:errors.slice(0,30),count:errors.length},null,2));process.exit(1)}
const report={status:'NOT_BET_ELIGIBLE',markets:{},notes:['Market skill requires genuine timestamped two-way sportsbook quotes and independently archived pregame forecasts.','No probabilities or sportsbook prices are inferred from results.','Positive retrospective ROI alone is not proof of future profitability.']};
for(const [name,a] of Object.entries(market)){
 const n=a.length,brier=mean(a.map(x=>(x.p-x.y)**2)),base=mean(a.map(x=>(x.p0-x.y)**2));
 const eps=1e-12,logloss=mean(a.map(x=>-x.y*Math.log(Math.max(eps,x.p))-(1-x.y)*Math.log(Math.max(eps,1-x.p))));
 const ece=Array.from({length:10},(_,i)=>a.filter(x=>Math.min(9,Math.floor(x.p*10))===i)).filter(x=>x.length).reduce((s,g)=>s+g.length/n*Math.abs(mean(g.map(x=>x.p))-mean(g.map(x=>x.y))),0);
 const sorted=a.slice().sort((x,y)=>date(x.r.kickoff)-date(y.r.kickoff));
 const split=Math.floor(sorted.length*.8),hold=sorted.slice(split);
 const distinctHoldoutEvents=new Set(hold.map(x=>x.r.event_id)).size;
 const holdBrier=hold.length?mean(hold.map(x=>(x.p-x.y)**2)):null;
 const holdBase=hold.length?mean(hold.map(x=>(x.p0-x.y)**2)):null;
 report.markets[name]={n,brier,market_brier:base,brier_skill:base>0?1-brier/base:null,log_loss:logloss,ece,holdout_n:hold.length,holdout_events:distinctHoldoutEvents,minimum_evidence_met:n>=200&&distinctHoldoutEvents>=30,holdout_brier:holdBrier,holdout_market_brier:holdBase,holdout_skill:holdBase>0?1-holdBrier/holdBase:null,eligible:false};
}
console.log(JSON.stringify(report,null,2));
