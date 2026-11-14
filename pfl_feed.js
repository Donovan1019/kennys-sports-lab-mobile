/* Shared PFL browser data loader. Never promotes research snapshots to betting-ready picks. */
(function(root){'use strict';
async function json(path){const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error(path+': HTTP '+r.status);return r.json()}
async function load(){
 const [events,readiness,intake,features,projections]=await Promise.allSettled([
 json('./data/pfl/events.json'),json('./data/pfl/bout-readiness.json'),
 json('./data/pfl/model-market-intake.json'),json('./data/pfl/historical-features.json'),json('./data/pfl/projections.json')
 ]);
 const get=r=>r.status==='fulfilled'?r.value:null;
 const snapshot=get(events),boutReadiness=get(readiness),marketIntake=get(intake),history=get(features),projectionData=get(projections);
 const verified=new Map((boutReadiness?.bouts||[]).map(b=>[String(b.boutId),b]));
 const markets=(marketIntake?.markets||[]).filter(m=>verified.get(String(m.fightId))?.identityAndHistoryVerified===true);
 return {snapshot,boutReadiness,marketIntake,history,projections:projectionData,markets,errors:{events:events.status==='rejected'?String(events.reason):null,readiness:readiness.status==='rejected'?String(readiness.reason):null,intake:intake.status==='rejected'?String(intake.reason):null,history:features.status==='rejected'?String(features.reason):null,projections:projections.status==='rejected'?String(projections.reason):null},bettingReady:false};
}
root.KSLPFLFeed=Object.freeze({load});
})(typeof window!=='undefined'?window:globalThis);
