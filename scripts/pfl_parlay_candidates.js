#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
function build(consensus,{iterations=50000,seed=20261114,now=Date.now()}={}){
 if(!Number.isInteger(iterations)||iterations<50000)throw Error('50K simulations required');
 const candidates=(consensus.rows||[]).filter(r=>Number.isFinite(Date.parse(r.recordedAt))&&Date.parse(r.recordedAt)<=now+300000&&now-Date.parse(r.recordedAt)<=7200000).filter(r=>r.markets?.length===2&&r.markets.every(m=>Number.isInteger(m.american)&&Math.abs(m.american)>=100)).map(r=>{
  const a=r.markets[0],b=r.markets[1];
  const implied=n=>n<0?-n/(-n+100):100/(n+100);
  const pa=implied(a.american),pb=implied(b.american),fair=pa/(pa+pb);
  const side=fair>=.5?0:1,chosen=r.markets[side];
  return {fightId:r.fightId,eventId:r.eventId,selection:chosen.selection,american:chosen.american,probability:side===0?fair:1-fair,recordedAt:r.recordedAt,source:r.source};
 }).sort((a,b)=>b.probability-a.probability);
 const totals=(consensus.rows||[]).flatMap(r=>(r.totalRounds||[]).filter(t=>Number.isFinite(t.line)&&[t.over?.american,t.under?.american].every(n=>Number.isInteger(n)&&Math.abs(n)>=100)&&Number.isFinite(Date.parse(t.recordedAt))&&Date.parse(t.recordedAt)<=now+300000&&now-Date.parse(t.recordedAt)<=7200000).map(t=>{const implied=n=>n<0?-n/(-n+100):100/(n+100);const a=implied(t.over.american),b=implied(t.under.american),prob=a/(a+b),over=prob>=.5;return {fightId:r.fightId,eventId:r.eventId,selection:(over?'Over ':'Under ')+t.line+' rounds',american:over?t.over.american:t.under.american,probability:over?prob:1-prob,recordedAt:t.recordedAt,source:r.source,line:t.line};}));
 let state=seed>>>0;const random=()=>((state=(Math.imul(state,1664525)+1013904223)>>>0)/4294967296);
 const parlays=[];
 for(const market of ['ml','totals'])for(const strategy of ['gold','silver','bronze'])for(const legs of [2,3,4,5]){
  const pool=market==='ml'?candidates:totals;
  if(new Set(pool.map(x=>x.fightId)).size<legs)continue;
  const ordered=[...pool].sort((a,b)=>strategy==='gold'?b.probability-a.probability:strategy==='bronze'?a.probability-b.probability:Math.abs(b.probability-.65)-Math.abs(a.probability-.65));
  const chosen=[],seen=new Set();for(const x of ordered){if(seen.has(x.fightId))continue;seen.add(x.fightId);chosen.push(x);if(chosen.length===legs)break;}if(chosen.length!==legs)continue;
  let hits=0;for(let i=0;i<iterations;i++){let success=true;for(const x of chosen)if(random()>=x.probability)success=false;if(success)hits++}
  const decimal=chosen.reduce((n,x)=>n*(x.american<0?1+100/-x.american:1+x.american/100),1);
  parlays.push({market,strategy,legs,markets:chosen,referenceDecimalOdds:decimal,referenceProbability:hits/iterations,referenceEV:(hits/iterations)*decimal-1,negativeEVWarning:(hits/iterations)*decimal-1<=0,iterations,simulation:'independent Bernoulli using consensus no-vig probabilities',crossFightIndependenceValidated:false,modelCalibrated:false,bookVerified:false,bettingReady:false,classification:'MARKET REFERENCE ONLY — NOT A BETTING RECOMMENDATION'});
 }
 return {schemaVersion:1,source:'pfl-consensus-parlay-candidates',generatedAt:new Date().toISOString(),candidateFights:candidates.length,totalRoundMarkets:totals.length,parlays,bettingReady:false};
}
if(require.main===module){const input=JSON.parse(fs.readFileSync('data/pfl/consensus-markets.json','utf8'));const out=build(input);fs.writeFileSync('data/pfl/parlay-candidates.json',JSON.stringify(out,null,2)+'\n');console.log('PFL parlay candidate generation:',JSON.stringify({fights:out.candidateFights,totalRoundMarkets:out.totalRoundMarkets,parlays:out.parlays.map(x=>x.market+':'+x.strategy+':'+x.legs),bettingReady:false}));}
module.exports={build};
