/* Fail-closed independently sourced historical-game-log adapter. */
'use strict';
const {auditHistory}=require('./prizepicks_history_audit');
function verifySourcePayload(payload,now=Date.now()){
 const fail=reason=>({status:'UNAVAILABLE',reason,records:[]});
 if(!payload||payload.schema_version!==1||payload.status!=='VERIFIED_GAME_LOGS'||!Array.isArray(payload.records)||typeof payload.source!=='string'||!payload.source.trim()||!payload.generated_at)return fail('verified historical source payload missing');
 const generated=Date.parse(payload.generated_at);
 if(!Number.isFinite(now)||!Number.isFinite(generated)||generated>now+60000||now-generated>7*86400000)return fail('invalid historical source timestamp');
 const sources=payload.source==='MULTI_SOURCE_VERIFIED'&&Array.isArray(payload.sources)&&payload.sources.length>=2&&payload.sources.every(s=>typeof s==='string'&&s.trim()&&s!=='MULTI_SOURCE_VERIFIED')&&new Set(payload.sources).size===payload.sources.length?new Set(payload.sources):new Set([payload.source]);
 if(payload.source==='MULTI_SOURCE_VERIFIED'&&sources.size<2)return fail('invalid verified source manifest');
 const records=[];
 for(const r of payload.records){
  if(!r||r.independentlyVerified!==true||!r.source||!r.providerPlayerId||r.providerPlayerId!==r.playerId||!r.league||!r.market||!r.period||!Array.isArray(r.games)||!sources.has(r.source))continue;
  records.push(r);
 }
 return records.length?{status:'VERIFIED_HISTORY_INPUT',records,reason:null}:fail('no independently verified records');
}
function buildHistoryAudit(rawFeed,payload,now=Date.now()){
 const source=verifySourcePayload(payload,now);
 if(source.status!=='VERIFIED_HISTORY_INPUT')return {status:'UNAVAILABLE',reason:source.reason,coverage:{total:0,matched:0,unavailable:0},rows:[]};
 return auditHistory(rawFeed,source.records,now);
}
module.exports={verifySourcePayload,buildHistoryAudit};
