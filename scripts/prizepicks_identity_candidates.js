'use strict';
// Names select possible records only. They never verify provider identities.
const fs=require('node:fs');
function cleanName(v){return String(v||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'')}
function build(feed,nbaHistory,nhlHistory){
 const rows=[];
 for(const league of ['NBA','NHL']){
  const history=league==='NBA'?nbaHistory:nhlHistory;
  const historyIds=new Set((history?.records||[]).filter(r=>r.league===league).map(r=>String(r.playerId)));
  const byProvider=new Map();
  if(league==='NBA'){
   for(const c of history?.diagnostics?.identityCandidates||[]){
    const key=String(c.prizepicksPlayerId);
    if(!byProvider.has(key))byProvider.set(key,new Set());
    for(const id of c.espnCandidateIds||[])if(historyIds.has(String(id)))byProvider.get(key).add(String(id));
   }
  }else{
   // Roster-name matches are candidates only, never verified provider identities.
   for(const c of history?.diagnostics?.identityCandidates||[]){
    const key=String(c.prizepicksPlayerId);
    if(!byProvider.has(key))byProvider.set(key,new Set());
    for(const id of c.nhlCandidateIds||[])if(historyIds.has(String(id)))byProvider.get(key).add(String(id));
   }
  }
  const seen=new Set();
  for(const line of feed?.lines||[]){
   if(line.league!==league||!line.player_id)continue;
   const key=String(line.player_id);
   if(seen.has(key))continue;seen.add(key);
   const options=[...(byProvider.get(key)||[])];
   const names=(feed.lines||[]).filter(x=>x.league===league&&String(x.player_id)===key).map(x=>cleanName(x.player));
   const nameConflict=new Set(names).size>1;
   rows.push({league,prizepicksPlayerId:key,player:line.player,historySource:league==='NBA'?'espn-public-boxscore':'api-web.nhle.com/v1',historyCandidateIds:nameConflict?[]:options,verified:false,status:nameConflict?'CONFLICTING_PROVIDER_NAMES':options.length===1?'REQUIRES_INDEPENDENT_ID_EVIDENCE':options.length>1?'AMBIGUOUS':'NO_HISTORY_MATCH'});
  }
 }
 return {schema_version:1,generated_at:new Date().toISOString(),status:'UNVERIFIED_CANDIDATES_ONLY',verifiedMappings:0,rows};
}
if(require.main===module){
 const read=p=>{try{return JSON.parse(fs.readFileSync(p,'utf8'))}catch{return null}};
 const feed=read(process.env.PRIZEPICKS_FEED_PATH||'feed/prizepicks_lines.json');
 const nba=read(process.env.PRIZEPICKS_NBA_HISTORY_PATH||'feed/prizepicks_nba_verified_history.json');
 const nhl=read(process.env.PRIZEPICKS_NHL_HISTORY_PATH||'feed/prizepicks_nhl_verified_history.json');
 const output=build(feed,nba,nhl);const dest=process.env.PRIZEPICKS_IDENTITY_CANDIDATES_PATH||'feed/prizepicks_identity_candidates.json';
 fs.writeFileSync(dest,JSON.stringify(output,null,2)+'\n');
 console.log(JSON.stringify({status:output.status,candidates:output.rows.length,byLeague:Object.fromEntries(['NBA','NHL'].map(l=>[l,output.rows.filter(r=>r.league===l).length])),verifiedMappings:0}));
}
module.exports={build};
