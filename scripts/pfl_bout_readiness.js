#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
function build(events,history,reconciliation){
 const verified=new Set((reconciliation.verifiedMatches||[]).map(x=>x.citoEventId).filter(Boolean));
 const profiles=new Map((history.profiles||[]).filter(p=>p?.slug).map(p=>[p.slug,p]));
 const bouts=[];
 for(const event of events.events||[])for(const bout of event.bouts||[]){
  if(bout.status!=='scheduled')continue;
  const reasons=[];
  if(!verified.has(event.id))reasons.push('EVENT_NOT_CROSS_SOURCE_VERIFIED');
  if(!bout.id||!Array.isArray(bout.fighters)||bout.fighters.length!==2)reasons.push('BOUT_ID_OR_FIGHTERS_INVALID');
  const slugs=(bout.fighters||[]).map(f=>f.slug);
  if(slugs.some(s=>typeof s!=='string'||!s)||new Set(slugs).size!==2)reasons.push('FIGHTER_IDENTITIES_INVALID');
  for(const slug of slugs){const p=profiles.get(slug);if(!p?.profile||!Array.isArray(p.fights))reasons.push('FIGHTER_HISTORY_MISSING:'+String(slug))}
  bouts.push({eventId:event.id,boutId:bout.id||null,fighters:slugs,identityAndHistoryVerified:reasons.length===0,bettingReady:false,blockedReasons:[...reasons,'LIVE_ODDS_UNVERIFIED','MODEL_CALIBRATION_UNVERIFIED','MONTE_CARLO_UNVERIFIED']});
 }
 return {schemaVersion:1,source:'pfl-bout-readiness',generatedAt:new Date().toISOString(),scheduledBouts:bouts.length,identityAndHistoryVerified:bouts.filter(b=>b.identityAndHistoryVerified).length,bettingReadyBouts:0,bouts};
}
if(require.main===module){
 const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));
 const out=build(load('data/pfl/events.json'),load('data/pfl/fighter-histories.json'),load('data/pfl/source-reconciliation.json'));
 fs.writeFileSync('data/pfl/bout-readiness.json',JSON.stringify(out,null,2)+'\n');
 console.log('PFL bout readiness:',JSON.stringify({scheduled:out.scheduledBouts,identityAndHistoryVerified:out.identityAndHistoryVerified,bettingReady:out.bettingReadyBouts}));
}
module.exports={build};
