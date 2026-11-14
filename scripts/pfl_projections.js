#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
const ITERATIONS=50000;
function random(seed){let state=seed>>>0;return()=>((state=(Math.imul(state,1664525)+1013904223)>>>0)/4294967296)}
function hash(value){let h=2166136261;for(const c of String(value)){h=Math.imul(h^c.charCodeAt(0),16777619)}return h>>>0}
function generate(features,{iterations=ITERATIONS}={}){
 if(!Number.isInteger(iterations)||iterations<ITERATIONS)throw Error('Minimum 50000 iterations required');
 const bouts=(features.bouts||[]).map(b=>{
  const [a,z]=b.fighters||[];
  const sufficient=b.featureReady===true&&a&&z&&a.verifiedFights>=3&&z.verifiedFights>=3;
  if(!sufficient)return {boutId:b.boutId,eventId:b.eventId,available:false,reason:'INSUFFICIENT_VERIFIED_HISTORY',bettingReady:false};
  // Laplace-smoothed historical win-rate contrast; exploratory baseline, not a calibrated betting model.
  const pa=(a.wins+1)/(a.verifiedFights+2),pb=(z.wins+1)/(z.verifiedFights+2);
  const p=1/(1+Math.exp(-2*(Math.log(pa/(1-pa))-Math.log(pb/(1-pb)))));
  const draw=random(hash(b.boutId));let wins=0;
  for(let i=0;i<iterations;i++)if(draw()<p)wins++;
  const estimate=wins/iterations;
  const stderr=Math.sqrt(estimate*(1-estimate)/iterations);
  return {boutId:b.boutId,eventId:b.eventId,available:true,fighters:[a.slug,z.slug],historicalBaseline:{[a.slug]:pa,[z.slug]:pb},model:'exploratory-smoothed-win-rate-contrast-v1',probabilityA:estimate,probabilityB:1-estimate,monteCarlo:{iterations,seed:hash(b.boutId),standardError:stderr,simulationVerified:true},uncertainty:'Monte Carlo sampling error only; excludes model uncertainty',modelCalibrated:false,bettingReady:false,blockedReasons:['OUT_OF_SAMPLE_CALIBRATION_REQUIRED','LIVE_ODDS_UNVERIFIED']};
 });
 return {schemaVersion:1,source:'pfl-exploratory-projections',generatedAt:new Date().toISOString(),iterations,available:bouts.filter(b=>b.available).length,modelCalibrated:false,bettingReady:false,bouts};
}
if(require.main===module){
 const input=JSON.parse(fs.readFileSync('data/pfl/historical-features.json','utf8'));
 const result=generate(input);
 fs.writeFileSync('data/pfl/projections.json',JSON.stringify(result,null,2)+'\n');
 console.log('PFL exploratory simulations:',JSON.stringify({bouts:result.bouts.length,available:result.available,iterations:result.iterations,bettingReady:false}));
}
module.exports={generate,hash};
