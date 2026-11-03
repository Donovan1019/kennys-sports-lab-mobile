/* Automated research audit from independently supplied verified history artifacts. */
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {buildCrossSourceHistoryAudit}=require('./prizepicks_history_identity');
const {bridgeNflverseArchive}=require('./prizepicks_nflverse_bridge');
const {verifySourcePayload}=require('./prizepicks_history_source');
function readJson(file){try{return JSON.parse(fs.readFileSync(file,'utf8'))}catch{return null}}
function runAudit(feed,history,crosswalk,now=Date.now()){
 if(!feed||feed.status!=='RAW_LINES_ONLY'||!Array.isArray(feed.lines))return {status:'UNAVAILABLE',reason:'fresh raw lines missing',coverage:{total:0,matched:0,unavailable:0},rows:[],betEligible:false};
 const observed=Date.parse(feed.generated_at||'');
 if(!Number.isFinite(observed)||observed>now+60000||now-observed>30*60*1000)return {status:'UNAVAILABLE',reason:'raw lines timestamp missing or stale',coverage:{total:feed.lines.length,matched:0,unavailable:feed.lines.length},rows:[],betEligible:false};
 const audit=buildCrossSourceHistoryAudit(feed,history,crosswalk,now);
 return {...audit,betEligible:false,modelValidated:false,sourceStatus:audit.status==='PARTIAL_HISTORY'?'VERIFIED_RESEARCH_ONLY':'UNAVAILABLE'};
}
function historySourceDiagnostics(explicitHistory,archive,now=Date.now()){
 const explicit=explicitHistory?verifySourcePayload(explicitHistory,now):null;
 const bridged=bridgeNflverseArchive(archive,now);
 return {explicitHistory:explicit?{status:explicit.status,reason:explicit.reason||null}:{status:'NOT_CONFIGURED'},nflArchive:{status:bridged.status,reason:bridged.reason||null},selected:explicit?.status==='VERIFIED_HISTORY_INPUT'?'EXPLICIT':bridged.status==='VERIFIED_GAME_LOGS'?'NFL_ARCHIVE':'NONE'};
}
function chooseVerifiedHistory(explicitHistory,archive,now=Date.now()){
 if(explicitHistory&&verifySourcePayload(explicitHistory,now).status==='VERIFIED_HISTORY_INPUT')return explicitHistory;
 const bridged=bridgeNflverseArchive(archive,now);
 return bridged.status==='VERIFIED_GAME_LOGS'?bridged:null;
}
function identityReadiness(feed,history,crosswalk){
 const lines=Array.isArray(feed?.lines)?feed.lines:[];
 const providerIds=new Set(lines.filter(x=>x.player_id).map(x=>[x.league,x.player_id].join('|')));
 const historyIds=new Set((history?.records||[]).filter(x=>x.playerId).map(x=>[x.league,x.playerId,x.source].join('|')));
 const mappings=Array.isArray(crosswalk)?crosswalk:[];
 const verified=mappings.filter(m=>m?.verified===true);
 const usable=verified.filter(m=>providerIds.has([m.league,m.prizepicksPlayerId].join('|'))&&historyIds.has([m.league,m.historyPlayerId,m.historySource].join('|')));
 const byProvider=new Map(),byHistory=new Map();
 for(const m of usable){
  const p=[m.league,m.prizepicksPlayerId,m.historySource].join('|');
  const h=[m.league,m.historyPlayerId,m.historySource].join('|');
  byProvider.set(p,(byProvider.get(p)||0)+1);
  byHistory.set(h,(byHistory.get(h)||0)+1);
 }
 const conflictingProviderKeys=new Set([...byProvider].filter(([,n])=>n>1).map(([k])=>k));
 const conflictingHistoryKeys=new Set([...byHistory].filter(([,n])=>n>1).map(([k])=>k));
 const safe=new Set(usable.filter(m=>!conflictingProviderKeys.has([m.league,m.prizepicksPlayerId,m.historySource].join('|'))&&!conflictingHistoryKeys.has([m.league,m.historyPlayerId,m.historySource].join('|'))).map(m=>[m.league,m.prizepicksPlayerId].join('|')));
 const byLeague={};
 for(const line of lines){
  const league=line?.league||'UNKNOWN';
  if(!byLeague[league])byLeague[league]={sourceLines:0,providerPlayers:0,historicalPlayerMarketRecords:0,verifiedPlayerMappings:0};
  byLeague[league].sourceLines++;
 }
 for(const key of providerIds){const league=key.split('|')[0];if(byLeague[league])byLeague[league].providerPlayers++;}
 for(const record of history?.records||[]){if(byLeague[record.league])byLeague[record.league].historicalPlayerMarketRecords++;}
 for(const key of safe){const league=key.split('|')[0];if(byLeague[league])byLeague[league].verifiedPlayerMappings++;}
 return {providerPlayers:providerIds.size,providerPlayersMissingId:lines.filter(x=>!x.player_id).length,historicalPlayerMarketRecords:history?.records?.length||0,verifiedMappingsProvided:verified.length,verifiedMappingsWithBothIdsPresent:usable.length,distinctProviderPlayersWithCandidateMappings:safe.size,conflictingProviderMappings:conflictingProviderKeys.size,conflictingHistoryMappings:conflictingHistoryKeys.size,automaticNameMatching:false,byLeague};
}
function main(){
 const now=Date.now();
 const feed=readJson(process.env.PRIZEPICKS_FEED_PATH||'feed/prizepicks_lines.json');
 const explicitHistory=process.env.PRIZEPICKS_HISTORY_PATH?readJson(process.env.PRIZEPICKS_HISTORY_PATH):null;
 const archive=readJson(process.env.PRIZEPICKS_NFL_ARCHIVE_PATH||'feed/nfl_player_stats.json');
 const history=chooseVerifiedHistory(explicitHistory,archive,now);
 const crosswalk=readJson(process.env.PRIZEPICKS_CROSSWALK_PATH||'feed/prizepicks_verified_crosswalk.json');
 const result=runAudit(feed,history,crosswalk,now);
 const output={schema_version:1,generated_at:new Date(now).toISOString(),...result,identityReadiness:identityReadiness(feed,history,crosswalk),historySourceDiagnostics:historySourceDiagnostics(explicitHistory,archive,now),inputs:{rawLines:feed?.status==='RAW_LINES_ONLY'?'PRESENT':'MISSING',historicalSource:history?.status==='VERIFIED_GAME_LOGS'?'PRESENT':'MISSING_OR_UNVERIFIED',verifiedCrosswalk:Array.isArray(crosswalk)&&crosswalk.length?'PRESENT':'MISSING',nflArchive:archive?.source==='nflverse-stats-player-week'?'FOUND':'MISSING_OR_UNRECOGNIZED'}};
 const dest=process.env.PRIZEPICKS_HISTORY_AUDIT_PATH||'feed/prizepicks_history_audit.json';
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,JSON.stringify(output,null,2)+'\n');
 console.log('PrizePicks history audit: '+output.status+'; '+(output.reason||'research only'));
}
if(require.main===module)main();
module.exports={readJson,runAudit,chooseVerifiedHistory,identityReadiness,historySourceDiagnostics};
