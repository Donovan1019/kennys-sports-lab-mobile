'use strict';
// Only explicit provider external IDs plus an independently collected historical ID qualify.
const fs=require('node:fs');
const {hasIdentityEvidence}=require('./prizepicks_history_identity');
function build(feed,nba,nhl,at=new Date().toISOString()){
 const rows=[],conflicts=[],histories={NBA:nba,NHL:nhl};
 for(const league of ['NBA','NHL']){
  const history=histories[league],source=league==='NBA'?'espn-public-boxscore':'api-web.nhle.com/v1',field=league==='NBA'?'espn':'nhl';
  const ids=new Set((history?.records||[]).filter(r=>r.league===league&&r.source===source).map(r=>String(r.playerId)));
  const grouped=new Map();
  for(const line of feed?.lines||[]){
   if(line.league!==league||!line.player_id)continue;
   const id=String(line.player_id),external=line.external_ids?.[field];
   if(!grouped.has(id))grouped.set(id,[]);
   grouped.get(id).push({line,external:external==null?'':String(external)});
  }
  for(const [providerId,entries] of grouped){
   const candidates=[...new Set(entries.map(e=>e.external).filter(Boolean))];
   if(candidates.length!==1||entries.some(e=>!e.external)||!ids.has(candidates[0])){
    if(candidates.length>1)conflicts.push({league,providerId,reason:'CONFLICTING_EXTERNAL_IDS'});
    continue;
   }
   const historyId=candidates[0];
   const first=entries[0].line;
   const historyReference=league==='NBA'?'https://www.espn.com/nba/player/_/id/'+encodeURIComponent(historyId):'https://www.nhl.com/player/'+encodeURIComponent(historyId);
   const mapping={league,prizepicksPlayerId:providerId,historyPlayerId:historyId,historySource:source,verified:true,evidence:{provider:'PrizePicksAPI.com',historySource:source,prizepicksPlayerId:providerId,historyPlayerId:historyId,providerReference:'PrizePicksAPI.com projection '+String(first.id),historyReference,checkedAt:at}};
   if(hasIdentityEvidence(mapping))rows.push(mapping);
  }
 }
 const reverse=new Map(),blocked=new Set();
 for(const m of rows){const k=m.league+'|'+m.historyPlayerId;if(reverse.has(k))blocked.add(k);reverse.set(k,m.prizepicksPlayerId)}
 const mappings=rows.filter(m=>!blocked.has(m.league+'|'+m.historyPlayerId));
 return {schema_version:1,generated_at:at,status:mappings.length?'EXPLICIT_EXTERNAL_IDS_VERIFIED':'UNAVAILABLE',verifiedMappings:mappings.length,conflicts,mappings};
}
if(require.main===module){
 const read=p=>{try{return JSON.parse(fs.readFileSync(p,'utf8'))}catch{return null}};
 const result=build(read(process.env.PRIZEPICKS_FEED_PATH||'feed/prizepicks_lines.json'),read(process.env.PRIZEPICKS_NBA_HISTORY_PATH||'feed/prizepicks_nba_verified_history.json'),read(process.env.PRIZEPICKS_NHL_HISTORY_PATH||'feed/prizepicks_nhl_verified_history.json'));
 fs.writeFileSync(process.env.PRIZEPICKS_CROSSWALK_PATH||'feed/prizepicks_verified_crosswalk.json',JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:result.status,verifiedMappings:result.verifiedMappings,conflicts:result.conflicts.length}));
}
module.exports={build};
