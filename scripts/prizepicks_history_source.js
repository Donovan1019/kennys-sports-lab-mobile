/* Fail-closed independently sourced historical-game-log adapter. */
'use strict';
const {auditHistory}=require('./prizepicks_history_audit');
function verifySourcePayload(payload){
 if(!payload||payload.schema_version!==1||payload.status!=='VERIFIED_GAME_LOGS'||!Array.isArray(payload.records)||!payload.source||!payload.generated_at)return {status:'UNAVAILABLE',reason:'verified historical source payload missing'};
 const generated=Date.parse(payload.generated_at);if(!Number.isFinite(generated)||generated>Date.now()+60000)return {status:'UNAVAILABLE',reason:'invalid historical source timestamp'};
 const records=[];for(const r of payload.records){if(!r||r.independentlyVerified!==true||!r.source||!r.providerPlayerId||r.providerPlayerId!==r.playerId||!r.league||!r.market||!r.period||!Array.isArray(r.games))continue;records.push(r)}
 return {status:records.length?'VERIFIED_HISTORY_INPUT':'UNAVAILABLE',records,reason:records.length?null:'no independently verified records'};
}
function buildHistoryAudit(rawFeed,payload,now=Date.now()){const source=verifySourcePayload(payload);if(source.status!=='VERIFIED_HISTORY_INPUT')return {status:'UNAVAILABLE',reason:source.reason,coverage:{total:0,matched:0,unavailable:0},rows:[]};return auditHistory(rawFeed,source.records,now)}
module.exports={verifySourcePayload,buildHistoryAudit};
