'use strict';
// Candidate IDs are never an authorization to join PrizePicks props to history.
const fs=require('node:fs');
const {attachVerifiedIdentity}=require('./prizepicks_history_identity');
function build(feed,history){
 const lines=(feed?.lines||[]).filter(x=>x.league==='NBA'&&x.player_id);
 const candidates=history?.diagnostics?.identityCandidates||[];
 const ids=new Set((history?.records||[]).filter(r=>r.league==='NBA').map(r=>String(r.playerId)));
 const byProvider=new Map();
 for(const c of candidates){
  const key=String(c.prizepicksPlayerId);
  const line=lines.find(x=>String(x.player_id)===key);
  if(!line||byProvider.has(key))continue;
  const options=[...new Set((c.espnCandidateIds||[]).map(String))].filter(id=>ids.has(id));
  byProvider.set(key,{league:'NBA',prizepicksPlayerId:key,player:line.player,historySource:'espn-public-boxscore',historyCandidateIds:options,verified:false,status:options.length===1?'REQUIRES_INDEPENDENT_ID_EVIDENCE':options.length?'AMBIGUOUS':'NO_HISTORY_MATCH'});
 }
 const rows=[...byProvider.values()];
 return {schema_version:1,generated_at:new Date().toISOString(),status:'UNVERIFIED_CANDIDATES_ONLY',verifiedMappings:0,rows};
}
if(require.main===module){const feed=JSON.parse(fs.readFileSync(process.env.PRIZEPICKS_FEED_PATH||'feed/prizepicks_lines.json'));const history=JSON.parse(fs.readFileSync(process.env.PRIZEPICKS_NBA_HISTORY_PATH||'feed/prizepicks_nba_verified_history.json'));const output=build(feed,history);const dest=process.env.PRIZEPICKS_IDENTITY_CANDIDATES_PATH||'feed/prizepicks_identity_candidates.json';fs.writeFileSync(dest,JSON.stringify(output,null,2)+'\n');console.log(JSON.stringify({status:output.status,candidates:output.rows.length,verifiedMappings:0}));}
module.exports={build};
