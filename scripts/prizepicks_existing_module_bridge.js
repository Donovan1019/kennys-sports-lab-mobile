'use strict';
/* Reuse existing Kenny's NBA and NHL player archives, preserving source IDs and market provenance.
   These IDs are ESPN/NHL IDs, never automatically PrizePicks IDs. */
const fs=require('node:fs');
const path=require('node:path');
const MARKETS={NBA:{Points:'Points',Rebounds:'Rebounds',Assists:'Assists',Threes:'3-Pointers Made',Steals:'Steals',Blocks:'Blocks',Turnovers:'Turnovers'},NHL:{Goals:'Goals',Assists:'Assists',Points:'Points','Shots on goal':'Shots on Goal','Blocked shots':'Blocked Shots',Saves:'Saves','Goals against':'Goals Against'}};
const SOURCE={NBA:'espn-public-boxscore',NHL:'nhl-official-boxscore'};
function adapt(snapshot,league,now=Date.now()){
 const source=SOURCE[league],out={schema_version:1,status:'UNAVAILABLE',source,generated_at:new Date(now).toISOString(),records:[],diagnostics:{reason:null,players:0,validGames:0,markets:0,sourceTimestamp:snapshot?.fetched_at||null}};
 if(!snapshot||snapshot.source!==source||snapshot.sport!==league.toLowerCase()||!Array.isArray(snapshot.players)){out.diagnostics.reason='existing '+league+' module snapshot missing or wrong source';return out}
 const timestamp=Date.parse(snapshot.fetched_at||'');
 if(!Number.isFinite(timestamp)||timestamp>now+60000||now-timestamp>7*86400000){out.diagnostics.reason='existing module snapshot older than 7 days';return out}
 const allowed=MARKETS[league];const seenIds=new Set();
 for(const player of snapshot.players){
  const id=String(player?.id||'');if(!/^\d+$/.test(id)||seenIds.has(id)||!Array.isArray(player.games))continue;
  seenIds.add(id);out.diagnostics.players++;
  for(const [original,market] of Object.entries(allowed)){
   const games=[],seen=new Set();
   for(const game of player.games){
    const gid=String(game?.game_id||''),date=String(game?.date||''),value=game?.values?.[original];
    if(!/^\d+$/.test(gid)||seen.has(gid)||!/^\d{4}-\d{2}-\d{2}$/.test(date)||typeof value!=='number'||!Number.isFinite(value)||value<0)continue;
    if((game.quality_flags||[]).some(flag=>/sog|shots/i.test(String(flag)))&&original==='Shots on goal')continue;
    const time=Date.parse(date+'T12:00:00Z');if(!Number.isFinite(time)||time>now)continue;
    seen.add(gid);games.push({eventId:gid,playedAt:new Date(time).toISOString(),verified:true,value});
   }
   if(games.length<15)continue;
   games.sort((a,b)=>Date.parse(a.playedAt)-Date.parse(b.playedAt));
   out.records.push({playerId:id,providerPlayerId:id,league,market,period:'Full game',source,independentlyVerified:true,games});
   out.diagnostics.validGames+=games.length;
  }
 }
 out.diagnostics.markets=out.records.length;
 if(out.records.length)out.status='VERIFIED_GAME_LOGS';
 else out.diagnostics.reason='no eligible player-market history with 15 verified games';
 return out;
}
function main(){
 for(const [league,sourcePath,dest] of [['NBA',process.env.KENNY_NBA_ARCHIVE_PATH||'feed/nba_player_stats.json','feed/prizepicks_nba_module_history.json'],['NHL',process.env.KENNY_NHL_ARCHIVE_PATH||'feed/nhl_official_player_stats.json','feed/prizepicks_nhl_module_history.json']]){
  let snapshot=null;try{snapshot=JSON.parse(fs.readFileSync(sourcePath,'utf8'))}catch{}
  const result=adapt(snapshot,league);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({league,status:result.status,records:result.records.length,reason:result.diagnostics.reason,source:result.source}));
 }
}
if(require.main===module)main();
module.exports={adapt};
