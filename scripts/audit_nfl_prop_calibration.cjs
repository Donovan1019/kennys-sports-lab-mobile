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
const validOdds=o=>Number.isInteger(o)&&(o>=100||o<=-100);
const implied=o=>o>0?100/(o+100):-o/(-o+100);
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const market={};
const errors=[];const seen=new Set();const firstSelection=new Map();
const validSelection=x=>x==='Over'||x==='Under';
const validMarket=x=>['player_pass_yds','player_rush_yds','player_reception_yds','player_receptions','player_pass_tds','player_rush_tds','player_anytime_td','player_rec_tds','Passing Yards','Rushing Yards','Receiving Yards','Receptions','Passing Touchdowns','Rushing Touchdowns','Receiving Touchdowns','Anytime Touchdown'].includes(x);
for(const [i,r] of rows.entries()){
 const key=[r.event_id,r.player,r.market,r.line,r.quoted_at,r.forecast_at].join('|');
 if(seen.has(key)){errors.push('duplicate snapshot '+i);continue}seen.add(key);
 if(!validMarket(r.market)||!r.event_id||!r.player||![r.kickoff,r.quoted_at,r.forecast_at,r.graded_at].every(validDate)||date(r.quoted_at)>=date(r.kickoff)||date(r.forecast_at)>=date(r.kickoff)||date(r.quoted_at)>date(r.forecast_at)||date(r.graded_at)<date(r.kickoff)){errors.push('invalid timing/identity '+i);continue}
 if(![r.line,r.outcome,r.model_probability,r.over_odds,r.under_odds].every(Number.isFinite)||r.model_probability<=0||r.model_probability>=1||!validOdds(r.over_odds)||!validOdds(r.under_odds)){errors.push('invalid numeric fields '+i);continue}
 if(date(r.forecast_at)-date(r.quoted_at)>6*60*60*1000){errors.push('stale sportsbook quote '+i);continue}
 if(r.selection!==undefined&&!validSelection(r.selection)){errors.push('invalid selection '+i);continue}
 if(r.bet_odds!==undefined&&(!validOdds(r.bet_odds)||!validSelection(r.selection))){errors.push('invalid bet odds or missing selection '+i);continue}
 if(r.outcome===r.line)continue; // pushes are neither wins nor losses
 const po=implied(r.over_odds),pu=implied(r.under_odds);
 if(!(po>0&&po<1&&pu>0&&pu<1&&po+pu>1)){errors.push('invalid prices '+i);continue}
 const p0=po/(po+pu),p=r.model_probability,y=Number(r.outcome>r.line);
 const selectionKey=[r.event_id,r.player,r.market,r.line].join('|');
 const previous=firstSelection.get(selectionKey);
 if(!previous||date(r.forecast_at)<date(previous.r.forecast_at))firstSelection.set(selectionKey,{p,p0,y,r});
}
for(const item of firstSelection.values())(market[item.r.market]??=[]).push(item);
if(errors.length){console.error(JSON.stringify({status:'FAIL_DATA_INTEGRITY',errors:errors.slice(0,30),count:errors.length},null,2));process.exit(1)}
const report={status:'NOT_BET_ELIGIBLE',markets:{},snapshot_deduplication:'earliest archived pregame forecast per event/player/market/line',holdout_grouping:'chronological event IDs; all selections from a game remain together',notes:['Market skill requires genuine timestamped two-way sportsbook quotes and independently archived pregame forecasts.','No probabilities or sportsbook prices are inferred from results.','Positive retrospective ROI alone is not proof of future profitability.']};
for(const [name,a] of Object.entries(market)){
 const n=a.length,brier=mean(a.map(x=>(x.p-x.y)**2)),base=mean(a.map(x=>(x.p0-x.y)**2));
 const eps=1e-12,logloss=mean(a.map(x=>-x.y*Math.log(Math.max(eps,x.p))-(1-x.y)*Math.log(Math.max(eps,1-x.p))));
 const ece=Array.from({length:10},(_,i)=>a.filter(x=>Math.min(9,Math.floor(x.p*10))===i)).filter(x=>x.length).reduce((s,g)=>s+g.length/n*Math.abs(mean(g.map(x=>x.p))-mean(g.map(x=>x.y))),0);
 const sorted=a.slice().sort((x,y)=>date(x.r.kickoff)-date(y.r.kickoff));
 const events=new Map();for(const x of sorted){const id=x.r.event_id;const kickoff=date(x.r.kickoff);if(!events.has(id)||kickoff<events.get(id))events.set(id,kickoff)}
 const eventOrder=[...events].sort((a,b)=>a[1]-b[1]||a[0].localeCompare(b[0]));
 const holdoutIds=new Set(eventOrder.slice(Math.floor(eventOrder.length*.8)).map(x=>x[0]));
 const hold=sorted.filter(x=>holdoutIds.has(x.r.event_id));
 const distinctHoldoutEvents=new Set(hold.map(x=>x.r.event_id)).size;
 const holdBrier=hold.length?mean(hold.map(x=>(x.p-x.y)**2)):null;
 const holdBase=hold.length?mean(hold.map(x=>(x.p0-x.y)**2)):null;
 report.markets[name]={n,brier,market_brier:base,brier_skill:base>0?1-brier/base:null,log_loss:logloss,ece,holdout_n:hold.length,holdout_events:distinctHoldoutEvents,unique_events:eventOrder.length,minimum_evidence_met:n>=200&&distinctHoldoutEvents>=30&&eventOrder.length>=40,holdout_brier:holdBrier,holdout_market_brier:holdBase,holdout_skill:holdBase>0?1-holdBrier/holdBase:null,eligible:false};
}
if(process.env.KSL_PROP_REPORT_PATH){fs.mkdirSync(require('node:path').dirname(process.env.KSL_PROP_REPORT_PATH),{recursive:true});fs.writeFileSync(process.env.KSL_PROP_REPORT_PATH,JSON.stringify({...report,generated_at:new Date().toISOString()},null,2)+'\n')}
console.log(JSON.stringify(report,null,2));
