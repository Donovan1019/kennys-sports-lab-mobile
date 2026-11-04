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
 const explicit=Array.isArray(explicitHistory)?explicitHistory.map(item=>item?verifySourcePayload(item,now):{status:'NOT_CONFIGURED'}):explicitHistory?verifySourcePayload(explicitHistory,now):null;
 const bridged=bridgeNflverseArchive(archive,now);
 return {explicitHistory:Array.isArray(explicit)?explicit.map(item=>({status:item.status,reason:item.reason||null})):explicit?{status:explicit.status,reason:explicit.reason||null}:{status:'NOT_CONFIGURED'},nflArchive:{status:bridged.status,reason:bridged.reason||null},selected:(Array.isArray(explicit)?explicit.some(item=>item.status==='VERIFIED_HISTORY_INPUT'):explicit?.status==='VERIFIED_HISTORY_INPUT')?'EXPLICIT':bridged.status==='VERIFIED_GAME_LOGS'?'NFL_ARCHIVE':'NONE'};
}
function chooseVerifiedHistory(explicitHistory,archive,now=Date.now()){
 const explicitInputs=Array.isArray(explicitHistory)?explicitHistory:[explicitHistory];
 const explicit=explicitInputs.filter(item=>item&&verifySourcePayload(item,now).status==='VERIFIED_HISTORY_INPUT').map(item=>({...item,records:verifySourcePayload(item,now).records}));
 const bridged=bridgeNflverseArchive(archive,now);
 const nfl=bridged.status==='VERIFIED_GAME_LOGS'?bridged:null;
 const inputs=[...explicit,...(nfl?[nfl]:[])];
 if(!inputs.length)return null;
 if(inputs.length===1)return inputs[0];
 const sources=inputs.map(item=>item.source);
 if(new Set(sources).size!==sources.length)return null;
 const keys=new Set();
 const records=[];
 for(const record of inputs.flatMap(item=>item.records)){
  const key=[record.league,record.playerId,record.market,record.period,record.source].join('|');
  if(keys.has(key))return null;
  keys.add(key);records.push(record);
 }
 return {schema_version:1,status:'VERIFIED_GAME_LOGS',source:'MULTI_SOURCE_VERIFIED',sources,generated_at:new Date(now).toISOString(),records};
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
 const exactIdOverlapByLeague={};
 for(const key of providerIds){const [league,id]=key.split('|');if([...historyIds].some(h=>h.startsWith(league+'|'+id+'|')))exactIdOverlapByLeague[league]=(exactIdOverlapByLeague[league]||0)+1;}
 for(const line of lines){
  const league=line?.league||'UNKNOWN';
  if(!byLeague[league])byLeague[league]={sourceLines:0,providerPlayers:0,historicalPlayerMarketRecords:0,verifiedPlayerMappings:0};
  byLeague[league].sourceLines++;
 }
 for(const key of providerIds){const league=key.split('|')[0];if(byLeague[league])byLeague[league].providerPlayers++;}
 for(const record of history?.records||[]){if(byLeague[record.league])byLeague[record.league].historicalPlayerMarketRecords++;}
 for(const key of safe){const league=key.split('|')[0];if(byLeague[league])byLeague[league].verifiedPlayerMappings++;}
 return {providerPlayers:providerIds.size,providerPlayersMissingId:lines.filter(x=>!x.player_id).length,historicalPlayerMarketRecords:history?.records?.length||0,verifiedMappingsProvided:verified.length,verifiedMappingsWithBothIdsPresent:usable.length,distinctProviderPlayersWithCandidateMappings:safe.size,conflictingProviderMappings:conflictingProviderKeys.size,conflictingHistoryMappings:conflictingHistoryKeys.size,automaticNameMatching:false,unverifiedExactIdOverlaps:exactIdOverlapByLeague,byLeague};
}
function marketReadiness(feed,history){
 const lines=Array.isArray(feed?.lines)?feed.lines:[];
 const {canonicalMarket}=require('./prizepicks_history_join');
 const available=new Set((history?.records||[]).map(r=>[r.league,r.market,r.period].join('|')));
 const byLeague={};
 for(const line of lines){
  const league=line.league||'UNKNOWN',market=line.market||'UNKNOWN';
  const group=byLeague[league]??={sourceLines:0,markets:{},supportedLines:0,unsupportedLines:0};
  const key=[league,canonicalMarket(league,market),line.period].join('|');
  const supported=available.has(key);
  group.sourceLines++;
  if(supported)group.supportedLines++;else group.unsupportedLines++;
  const entry=group.markets[market]??={lines:0,historyMarket:canonicalMarket(league,market),historyMarketAvailable:false};
  entry.lines++;entry.historyMarketAvailable=entry.historyMarketAvailable||supported;
 }
 return byLeague;
}
function main(){
 const now=Date.now();
 const feed=readJson(process.env.PRIZEPICKS_FEED_PATH||'feed/prizepicks_lines.json');
 const historyPaths=[process.env.PRIZEPICKS_HISTORY_PATH,process.env.PRIZEPICKS_NBA_HISTORY_PATH,process.env.PRIZEPICKS_NHL_HISTORY_PATH].filter(Boolean);
 const explicitHistory=historyPaths.length?historyPaths.map(readJson).filter(Boolean):null;
 const archive=readJson(process.env.PRIZEPICKS_NFL_ARCHIVE_PATH||'feed/nfl_player_stats.json');
 const archiveAudit=readJson(process.env.PRIZEPICKS_NFL_ARCHIVE_AUDIT_PATH||'feed/nfl_player_stats_audit.json');
 const history=chooseVerifiedHistory(explicitHistory,archive,now);
 const crosswalk=readJson(process.env.PRIZEPICKS_CROSSWALK_PATH||'feed/prizepicks_verified_crosswalk.json');
 const result=runAudit(feed,history,crosswalk,now);
 const output={schema_version:1,generated_at:new Date(now).toISOString(),...result,identityReadiness:identityReadiness(feed,history,crosswalk),marketReadiness:marketReadiness(feed,history),historySourceDiagnostics:{...historySourceDiagnostics(explicitHistory,archive,now),archiveAudit:{status:archiveAudit?.status||'MISSING',gameCount:archiveAudit?.game_count??null,playerCount:archiveAudit?.player_count??null}},inputs:{rawLines:feed?.status==='RAW_LINES_ONLY'?'PRESENT':'MISSING',historicalSource:history?.status==='VERIFIED_GAME_LOGS'?'PRESENT':'MISSING_OR_UNVERIFIED',verifiedCrosswalk:Array.isArray(crosswalk)&&crosswalk.length?'PRESENT':'MISSING',nflArchive:archive?.source==='nflverse-stats-player-week'?'FOUND':'MISSING_OR_UNRECOGNIZED'}};
 const dest=process.env.PRIZEPICKS_HISTORY_AUDIT_PATH||'feed/prizepicks_history_audit.json';
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,JSON.stringify(output,null,2)+'\n');
 console.log('PrizePicks history audit: '+output.status+'; '+(output.reason||'research only'));
}
if(require.main===module)main();
module.exports={readJson,runAudit,chooseVerifiedHistory,identityReadiness,historySourceDiagnostics,marketReadiness};
