/* PFL parlay construction: verified distinct fights only; no invented market data. */
(function(root){'use strict';
function rng(seed){let s=seed>>>0;return()=>((s=(Math.imul(s,1664525)+1013904223)>>>0)/4294967296)}
function build(markets,opts={}){
const errors=[];const legs=Number(opts.legs);const strategy=opts.strategy||'silver',type=opts.market||'both',iterations=opts.iterations||50000;
if(!Number.isInteger(legs)||legs<2||legs>5)return {eligible:false,errors:['Choose 2–5 legs']};
if(!['gold','silver','bronze'].includes(strategy)||!['both','ml','totals'].includes(type))return {eligible:false,errors:['Invalid strategy or market']};
if(!Number.isInteger(iterations)||iterations<50000)return {eligible:false,errors:['50k simulations required']};
if(opts.crossFightIndependenceValidated!==true)return {eligible:false,errors:['Cross-fight correlation model not validated']};
if(!Number.isInteger(opts.seed))return {eligible:false,errors:['Reproducible simulation seed required']};
const qualified=(Array.isArray(markets)?markets:[]).map(m=>({m,a:root.KSLPFLBets.assess(m,opts.now)}))
.filter(x=>x.a.eligible&&x.a.positiveEV&&(type==='both'||(type==='ml'?x.m.market==='ml':x.m.market==='total')));
qualified.sort((a,b)=>strategy==='gold'?b.m.probability-a.m.probability:strategy==='bronze'?b.a.ev-a.a.ev:(b.a.ev+b.m.probability)-(a.a.ev+a.m.probability));
const minTarget=opts.targetMinAmerican,maxTarget=opts.targetMaxAmerican;
const targeting=minTarget!==undefined||maxTarget!==undefined;
if(targeting&&(!Number.isFinite(minTarget)||!Number.isFinite(maxTarget)||minTarget<100||maxTarget<minTarget))
 return {eligible:false,errors:['Invalid positive American odds target range']};
const decimal=o=>root.KSLPFLMath.americanToDecimal(o);
const chosen=[],seen=new Set();
if(targeting){
 // Bounded combination search: distinct bouts, eligible positive-EV markets only.
 // Select highest modeled joint win chance within the requested payout range.
 const pool=qualified.slice(0,40);let best=null,bestP=-1;
 function search(start,picks,price,prob){
  if(picks.length===legs){
   const american=(price-1)*100;
   if(american>=minTarget&&american<=maxTarget&&prob>bestP){best=picks.slice();bestP=prob}
   return;
  }
  for(let i=start;i<pool.length;i++){
   const x=pool[i];if(picks.some(p=>p.m.fightId===x.m.fightId))continue;
   const nextPrice=price*decimal(x.m.odds);
   if((nextPrice-1)*100>maxTarget)continue;
   picks.push(x);search(i+1,picks,nextPrice,prob*x.m.probability);picks.pop();
  }
 }
 search(0,[],1,1);
 if(!best)return {eligible:false,errors:['No verified positive-EV distinct-fight parlay in requested odds range']};
 chosen.push(...best);
}else{
 for(const x of qualified){if(seen.has(x.m.fightId))continue;seen.add(x.m.fightId);chosen.push(x);if(chosen.length===legs)break}
}
if(chosen.length<legs)return {eligible:false,errors:['Insufficient distinct, verified, positive-EV fights for requested parlay'],available:chosen.length};
const random=rng(opts.seed);let hits=0;for(let i=0;i<iterations;i++){let win=true;for(const x of chosen){if(random()>=x.m.probability)win=false}if(win)hits++}
const jointProbability=hits/iterations;
const audited=root.KSLPFLMath.auditParlay(chosen.map(x=>({fightId:x.m.fightId,market:x.m.market,verified:true,fresh:true,simulated:true,calibrated:true,probability:x.m.probability,odds:x.m.odds})),{crossFightIndependenceValidated:true,simulationVerified:true,jointProbability});
if(!audited.eligible)return audited;
const stake=Number(opts.stake);if(!Number.isFinite(stake)||stake<=0)return {eligible:false,errors:['Positive stake required']};
return {...audited,eligible:true,legs:chosen.map(x=>({...x.m,individualEV:x.a.ev,fairOdds:x.a.fairOdds})),stake,potentialReturn:stake*audited.decimalOdds,netProfit:stake*(audited.decimalOdds-1),iterations,seed:opts.seed,method:'independent-fight Monte Carlo; validated cross-fight independence assumption required'};
}
root.KSLPFLParlays=Object.freeze({build});
})(typeof window!=='undefined'?window:globalThis);
