/* NCAA research probability audit. Never enable betting verdicts without historical calibration. */
(function(){
'use strict';
const norm=s=>String(s||'').toLowerCase().replace(/\bst\.?\b/gi,'state').replace(/[^a-z0-9]/g,'');
const erf=x=>{const sign=x<0?-1:1;const z=Math.abs(x),t=1/(1+.3275911*z);return sign*(1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-.284496736)*t+.254829592)*t*Math.exp(-z*z))};
const cdf=z=>(1+erf(z/Math.sqrt(2)))/2;
function independentHoldout(rows){
 const clean=(rows||[]).filter(r=>typeof r.date==='string'&&[r.a_pred,r.b_pred,r.a_actual,r.b_actual].every(Number.isFinite)).slice().sort((a,b)=>a.date.localeCompare(b.date));
 const days=[...new Set(clean.map(r=>r.date))];
 if(days.length<20||clean.length<300)return {ready:false,reason:'INSUFFICIENT_TEMPORAL_HOLDOUT',games:clean.length};
 const boundary=days[Math.floor(days.length*.7)];
 const train=clean.filter(r=>r.date<boundary),test=clean.filter(r=>r.date>=boundary);
 if(train.length<200||test.length<75)return {ready:false,reason:'INSUFFICIENT_TEMPORAL_HOLDOUT',trainGames:train.length,testGames:test.length};
 const residual=train.map(r=>(r.a_actual-r.b_actual)-(r.a_pred-r.b_pred));
 const sigma=Math.sqrt(residual.reduce((v,e)=>v+e*e,0)/residual.length);
 if(!Number.isFinite(sigma)||sigma<5||sigma>50)return {ready:false,reason:'INVALID_TRAIN_DISPERSION'};
 const bins=Array.from({length:10},()=>({n:0,p:0,w:0}));
 let brier=0,logLoss=0;
 for(const r of test){
  const p=Math.max(.000001,Math.min(.999999,cdf((r.a_pred-r.b_pred)/sigma)));
  const win=r.a_actual>r.b_actual?1:0;
  brier+=(p-win)**2;
  logLoss-=win*Math.log(p)+(1-win)*Math.log(1-p);
  const bin=bins[Math.min(9,Math.floor(p*10))];bin.n++;bin.p+=p;bin.w+=win;
 }
 const calibration=bins.filter(b=>b.n>=10).map(b=>({n:b.n,predicted:b.p/b.n,observed:b.w/b.n}));
 const baseline=test.reduce((n,r)=>n+(r.a_actual>r.b_actual?1:0),0)/test.length;
 const baselineBrier=test.reduce((v,r)=>v+(baseline-(r.a_actual>r.b_actual?1:0))**2,0)/test.length;
 return {ready:false,reason:'HOLDOUT_AUDIT_ONLY_NOT_CALIBRATED',trainGames:train.length,testGames:test.length,cutoffDate:boundary,sigma,brier:brier/test.length,logLoss:logLoss/test.length,baselineBrier,calibration};
}
function audit(research){
 const rows=(research?.evaluations||[]).filter(r=>[r.a_pred,r.b_pred,r.a_actual,r.b_actual].every(Number.isFinite));
 const reported=research?.walk_forward||{};
 if(!research?.research_only||!reported.sample_sufficient||rows.length<200||reported.games<200)return {ready:false,reason:'INSUFFICIENT_HISTORY',evaluations:rows.length};
 // Historical errors use strictly out-of-sample, previous-date predictions.
 const residual=rows.map(r=>(r.a_actual-r.b_actual)-(r.a_pred-r.b_pred));
 const sigma=Math.sqrt(residual.reduce((s,e)=>s+e*e,0)/residual.length);
 if(!Number.isFinite(sigma)||sigma<5||sigma>50)return {ready:false,reason:'INVALID_MARGIN_DISPERSION',evaluations:rows.length};
 const brier=rows.reduce((s,r)=>{const p=cdf((r.a_pred-r.b_pred)/sigma),actual=r.a_actual>r.b_actual?1:0;return s+(p-actual)**2},0)/rows.length;
 // This is an in-sample dispersion estimate on out-of-sample margins; not independent calibration.
 const holdout=independentHoldout(research.evaluations);
 return {ready:false,reason:'INDEPENDENT_CALIBRATION_REQUIRED',evaluations:rows.length,sigma,brier,holdout,preliminary:brier<.25};
}
function matchup(coverage,homeName,awayName){
 const teams=Object.values(coverage?.teams||{});
 const match=name=>{const hits=teams.filter(t=>norm(t.team)===norm(name));return hits.length===1?hits[0]:null};
 const home=match(homeName),away=match(awayName);
 if(!home||!away)return null;
 const pace=(home.pace+away.pace)/2;
 const margin=pace*(home.off+away.def-away.off-home.def)/200;
 return {margin,homeGames:home.games,awayGames:away.games};
}
function simulate(margin,sigma,seed=42,n=10000){
 if(!Number.isFinite(margin)||!Number.isFinite(sigma)||sigma<=0)return null;
 let state=seed>>>0,wins=0;
 const rand=()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return (state+.5)/4294967296};
 for(let i=0;i<n;i++){const z=Math.sqrt(-2*Math.log(rand()))*Math.cos(2*Math.PI*rand());if(margin+sigma*z>0)wins++}
 return {home:wins/n,away:1-wins/n,drawsExcluded:true,iterations:n};
}
window.NCAABProbability={audit,independentHoldout,matchup,simulate,cdf};
})();
