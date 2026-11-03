/* Automated research audit from independently supplied verified history artifacts. */
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {buildCrossSourceHistoryAudit}=require('./prizepicks_history_identity');
const {bridgeNflverseArchive}=require('./prizepicks_nflverse_bridge');
function readJson(file){try{return JSON.parse(fs.readFileSync(file,'utf8'))}catch{return null}}
function runAudit(feed,history,crosswalk,now=Date.now()){
 if(!feed||feed.status!=='RAW_LINES_ONLY'||!Array.isArray(feed.lines))return {status:'UNAVAILABLE',reason:'fresh raw lines missing',coverage:{total:0,matched:0,unavailable:0},rows:[],betEligible:false};
 const observed=Date.parse(feed.generated_at||'');
 if(!Number.isFinite(observed)||observed>now+60000||now-observed>30*60*1000)return {status:'UNAVAILABLE',reason:'raw lines timestamp missing or stale',coverage:{total:feed.lines.length,matched:0,unavailable:feed.lines.length},rows:[],betEligible:false};
 const audit=buildCrossSourceHistoryAudit(feed,history,crosswalk,now);
 return {...audit,betEligible:false,modelValidated:false,sourceStatus:audit.status==='PARTIAL_HISTORY'?'VERIFIED_RESEARCH_ONLY':'UNAVAILABLE'};
}
function chooseVerifiedHistory(explicitHistory,archive,now=Date.now()){
 if(explicitHistory)return explicitHistory;
 const bridged=bridgeNflverseArchive(archive,now);
 return bridged.status==='VERIFIED_GAME_LOGS'?bridged:null;
}
function main(){
 const now=Date.now();
 const feed=readJson(process.env.PRIZEPICKS_FEED_PATH||'feed/prizepicks_lines.json');
 const explicitHistory=process.env.PRIZEPICKS_HISTORY_PATH?readJson(process.env.PRIZEPICKS_HISTORY_PATH):null;
 const archive=readJson(process.env.PRIZEPICKS_NFL_ARCHIVE_PATH||'feed/nfl_player_stats.json');
 const history=chooseVerifiedHistory(explicitHistory,archive,now);
 const crosswalk=readJson(process.env.PRIZEPICKS_CROSSWALK_PATH||'feed/prizepicks_verified_crosswalk.json');
 const result=runAudit(feed,history,crosswalk,now);
 const output={schema_version:1,generated_at:new Date(now).toISOString(),...result,inputs:{rawLines:feed?.status==='RAW_LINES_ONLY'?'PRESENT':'MISSING',historicalSource:history?.status==='VERIFIED_GAME_LOGS'?'PRESENT':'MISSING_OR_UNVERIFIED',verifiedCrosswalk:Array.isArray(crosswalk)&&crosswalk.length?'PRESENT':'MISSING',nflArchive:archive?.source==='nflverse-stats-player-week'?'FOUND':'MISSING_OR_UNRECOGNIZED'}};
 const dest=process.env.PRIZEPICKS_HISTORY_AUDIT_PATH||'feed/prizepicks_history_audit.json';
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,JSON.stringify(output,null,2)+'\n');
 console.log('PrizePicks history audit: '+output.status+'; '+(output.reason||'research only'));
}
if(require.main===module)main();
module.exports={readJson,runAudit,chooseVerifiedHistory};
