/* Automated research audit from independently supplied verified history artifacts. */
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {buildCrossSourceHistoryAudit}=require('./prizepicks_history_identity');
function readJson(file){try{return JSON.parse(fs.readFileSync(file,'utf8'))}catch{return null}}
function runAudit(feed,history,crosswalk,now=Date.now()){
 if(!feed||feed.status!=='RAW_LINES_ONLY'||!Array.isArray(feed.lines))return {status:'UNAVAILABLE',reason:'fresh raw lines missing',coverage:{total:0,matched:0,unavailable:0},rows:[],betEligible:false};
 const observed=Date.parse(feed.generated_at||'');
 if(!Number.isFinite(observed)||observed>now+60000||now-observed>30*60*1000)return {status:'UNAVAILABLE',reason:'raw lines timestamp missing or stale',coverage:{total:feed.lines.length,matched:0,unavailable:feed.lines.length},rows:[],betEligible:false};
 const audit=buildCrossSourceHistoryAudit(feed,history,crosswalk,now);
 return {...audit,betEligible:false,modelValidated:false,sourceStatus:audit.status==='PARTIAL_HISTORY'?'VERIFIED_RESEARCH_ONLY':'UNAVAILABLE'};
}
function main(){
 const now=Date.now();
 const feed=readJson(process.env.PRIZEPICKS_FEED_PATH||'feed/prizepicks_lines.json');
 const history=process.env.PRIZEPICKS_HISTORY_PATH?readJson(process.env.PRIZEPICKS_HISTORY_PATH):null;
 const crosswalk=process.env.PRIZEPICKS_CROSSWALK_PATH?readJson(process.env.PRIZEPICKS_CROSSWALK_PATH):null;
 const result=runAudit(feed,history,crosswalk,now);
 const output={schema_version:1,generated_at:new Date(now).toISOString(),...result};
 const dest=process.env.PRIZEPICKS_HISTORY_AUDIT_PATH||'feed/prizepicks_history_audit.json';
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,JSON.stringify(output,null,2)+'\n');
 console.log('PrizePicks history audit: '+output.status+'; '+(output.reason||'research only'));
}
if(require.main===module)main();
module.exports={readJson,runAudit};
