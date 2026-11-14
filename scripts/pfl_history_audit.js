#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
function audit(snapshot){
 const profiles=Array.isArray(snapshot.profiles)?snapshot.profiles:[],issues=[],warnings=[],seen=new Set();
 let completed=0,verified=0,missing=0,conflicts=0,completeProfiles=0;
 for(const p of profiles){
  if(!p.slug||seen.has(p.slug))issues.push('Missing/duplicate fighter slug: '+p.slug);seen.add(p.slug);
  if(!p.profile||!Array.isArray(p.fights)){warnings.push('Profile or fight history unavailable: '+p.slug);missing++;continue}
  completeProfiles++;
  for(const f of p.fights){
   if(f.status!=='completed')continue;completed++;
   const perspective=f.perspective||{};
   const winner=f.winnerFighterSlug;
   const derived=winner?(winner===p.slug?'win':'loss'):null;
   if(perspective.fighterSlug&&perspective.fighterSlug!==p.slug){issues.push('Perspective identity mismatch: '+p.slug+' / '+f.id);continue}
   if(derived&&perspective.outcome&&derived!==perspective.outcome){issues.push('Winner/perspective mismatch: '+p.slug+' / '+f.id);continue}
   if(derived&&f.result&&f.result!==derived){conflicts++;warnings.push('Ambiguous top-level result; use winner and perspective: '+p.slug+' / '+f.id)}
   if(!derived||!perspective.outcome||!f.date||!f.method||!f.resultRound||!f.resultTime){missing++;continue}
   verified++;
  }
 }
 return {fighters:profiles.length,totalEligible:snapshot.totalEligible??null,completeProfiles,incompleteProfiles:profiles.length-completeProfiles,remainingEligible:Math.max(0,(snapshot.totalEligible??profiles.length)-completeProfiles),rateLimited:!!snapshot.rateLimited,completedFights:completed,verifiedPerspectiveResults:verified,missingResultFields:missing,ambiguousTopLevelResults:conflicts,issues,warnings,usableForHistoricalFeatures:issues.length===0&&verified>0,bettingReady:false};
}
if(require.main===module){const input=process.argv[2]||'data/pfl/fighter-histories.json';const result=audit(JSON.parse(fs.readFileSync(input,'utf8')));console.log(JSON.stringify(result,null,2));if(result.issues.length)process.exitCode=1}
module.exports={audit};
