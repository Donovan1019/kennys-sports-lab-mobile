#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
function features(history,readiness,asOf=new Date().toISOString()){
 const cutoff=Date.parse(asOf);
 if(!Number.isFinite(cutoff))throw Error('Invalid asOf date');
 const bySlug=new Map((history.profiles||[]).filter(p=>p&&typeof p.slug==='string').map(p=>[p.slug,p]));
 const fighters=new Map();
 function summarize(slug){
  if(fighters.has(slug))return fighters.get(slug);
  const profile=bySlug.get(slug),seen=new Set(),outcomes=[];
  for(const f of profile?.fights||[]){
   if(f?.status!=='completed'||!f.id||!f.date)continue;
   const timestamp=Date.parse(f.date);
   if(!Number.isFinite(timestamp)||timestamp>=cutoff||seen.has(f.id))continue;
   seen.add(f.id);
   const perspective=f.perspective||{};
   if(perspective.fighterSlug!==slug)continue;
   const derived=f.winnerFighterSlug===slug?'win':f.winnerFighterSlug?'loss':null;
   if(!derived||perspective.outcome!==derived)continue;
   outcomes.push({date:f.date,result:derived});
  }
  outcomes.sort((a,b)=>Date.parse(a.date)-Date.parse(b.date));
  const wins=outcomes.filter(x=>x.result==='win').length;
  const result={slug,verifiedFights:outcomes.length,wins,losses:outcomes.length-wins,winRate:outcomes.length?wins/outcomes.length:null,lastVerifiedFight:outcomes.at(-1)?.date??null};
  fighters.set(slug,result);return result;
 }
 const bouts=(readiness.bouts||[]).map(b=>{
  const pair=(b.fighters||[]).map(summarize);
  const reasons=[...(b.blockedReasons||[])];
  if(pair.length!==2||pair.some(p=>p.verifiedFights<3))reasons.push('INSUFFICIENT_VERIFIED_HISTORICAL_SAMPLE');
  return {boutId:b.boutId,eventId:b.eventId,fighters:pair,featureReady:b.identityAndHistoryVerified&&pair.length===2&&pair.every(p=>p.verifiedFights>=3),modelCalibrated:false,bettingReady:false,blockedReasons:[...new Set(reasons)]};
 });
 return {schemaVersion:1,source:'pfl-historical-features',generatedAt:new Date().toISOString(),asOf,featureReadyBouts:bouts.filter(b=>b.featureReady).length,bouts,bettingReady:false};
}
if(require.main===module){
 const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));
 const out=features(load('data/pfl/fighter-histories.json'),load('data/pfl/bout-readiness.json'));
 fs.writeFileSync('data/pfl/historical-features.json',JSON.stringify(out,null,2)+'\n');
 console.log('PFL historical features:',JSON.stringify({bouts:out.bouts.length,featureReady:out.featureReadyBouts,bettingReady:false}));
}
module.exports={features};
