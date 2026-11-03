/* Explicit, independently verified provider identity crosswalk. No name-based guessing. */
'use strict';
const {buildHistoryAudit}=require('./prizepicks_history_source');
function attachVerifiedIdentity(feed,payload,crosswalk){
 const fail=reason=>({status:'UNAVAILABLE',reason,records:[]});
 if(!feed||feed.status!=='RAW_LINES_ONLY'||!Array.isArray(feed.lines))return fail('raw provider lines missing');
 if(!payload||payload.schema_version!==1||payload.status!=='VERIFIED_GAME_LOGS'||!Array.isArray(payload.records))return fail('verified game-log payload missing');
 if(!Array.isArray(crosswalk)||!crosswalk.length)return fail('verified provider identity crosswalk missing');
 const bySource=new Map(),blocked=new Set(),reverse=new Map(),reverseBlocked=new Set();
 for(const m of crosswalk){
  if(!m||m.verified!==true||!m.league||!m.prizepicksPlayerId||!m.historyPlayerId||!m.historySource)continue;
  const k=[m.league,m.prizepicksPlayerId,m.historySource].join('|');
  if(bySource.has(k))blocked.add(k);
  bySource.set(k,m.historyPlayerId);
  const reverseKey=[m.league,m.historyPlayerId,m.historySource].join('|');
  if(reverse.has(reverseKey))reverseBlocked.add(reverseKey);
  reverse.set(reverseKey,m.prizepicksPlayerId);
 }
 const feedIds=new Set(feed.lines.filter(x=>x.player_id).map(x=>[x.league,x.player_id].join('|')));
 const records=[];
 for(const r of payload.records){
  if(!r||r.source!==payload.source||!r.playerId||!r.league||!r.market||!r.period)continue;
  for(const m of crosswalk){
   if(!m||m.verified!==true||m.league!==r.league||m.historySource!==r.source||m.historyPlayerId!==r.playerId)continue;
   const key=[m.league,m.prizepicksPlayerId,m.historySource].join('|');
   const reverseKey=[m.league,m.historyPlayerId,m.historySource].join('|');
   if(blocked.has(key)||reverseBlocked.has(reverseKey)||bySource.get(key)!==r.playerId||reverse.get(reverseKey)!==m.prizepicksPlayerId||!feedIds.has([m.league,m.prizepicksPlayerId].join('|')))continue;
   records.push({...r,providerPlayerId:m.prizepicksPlayerId,playerId:m.prizepicksPlayerId});
  }
 }
 return {status:records.length?'VERIFIED_IDENTITY_MAPPING':'UNAVAILABLE',reason:records.length?null:'no verified identity matches',records};
}
function buildCrossSourceHistoryAudit(feed,payload,crosswalk,now=Date.now()){
 const mapped=attachVerifiedIdentity(feed,payload,crosswalk);
 if(mapped.status!=='VERIFIED_IDENTITY_MAPPING'){
  const lines=Array.isArray(feed?.lines)?feed.lines:[];
  const byLeague={};
  for(const line of lines){const league=line?.league||'UNKNOWN';byLeague[league]=(byLeague[league]||0)+1;}
  return {status:'UNAVAILABLE',reason:mapped.reason,coverage:{total:lines.length,matched:0,unavailable:lines.length,byLeague},rows:[]};
 }
 return buildHistoryAudit(feed,{...payload,records:mapped.records},now);
}
module.exports={attachVerifiedIdentity,buildCrossSourceHistoryAudit};
