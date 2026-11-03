/* Fail-closed independently sourced historical-game-log adapter. */
'use strict';
const {auditHistory}=require('./prizepicks_history_audit');
function verifySourcePayload(payload,now=Date.now()){
 const fail=reason=>({status:'UNAVAILABLE',reason,records:[]});
 if(!payload||payload.schema_version!==1||payload.status!=='VERIFIED_GAME_LOGS'||!Array.isArray(payload.records)||typeof payload.source!=='string'||!payload.source.trim()||!payload.generated_at)return fail('verified historical source payload missing');
 const generated=Date.parse(payload.generated_at);
 if(!Number.isFinite(now)||!Number.isFinite(generated)||generated>now+60000||now-generated>7*86400000)return fail('invalid historical source timestamp');
 const records=[];
 for(const r of payload.records){
  if(!r||r.independentlyVerified!==true||!r.source||!r.providerPlayerId||r.providerPlayerId!==r.playerId||!r.league||!r.market||!r.period||!Array.isArray(r.games)||r.source!==payload.source)continue;
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
