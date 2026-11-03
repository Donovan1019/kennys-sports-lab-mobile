/* Reuse existing nflverse player-game archive, never infer identity or event dates. */
'use strict';
const MARKET_VALUES=Object.freeze({'Passing yards':'Passing yards','Rushing yards':'Rushing yards','Receiving yards':'Receiving yards','Receptions':'Receptions','Passing touchdowns':'Passing touchdowns','Rushing touchdowns':'Rushing touchdowns','Receiving touchdowns':'Receiving touchdowns'});
function bridgeNflverseArchive(archive,now=Date.now()){
 const fail=reason=>({status:'UNAVAILABLE',reason,records:[]});
 if(!archive||archive.source!=='nflverse-stats-player-week'||!Array.isArray(archive.players)||!archive.fetched_at)return fail('existing nflverse archive unavailable or unrecognized');
 const fetched=Date.parse(archive.fetched_at);
 if(!Number.isFinite(fetched)||fetched>now+60000||now-fetched>7*86400000)return fail('nflverse archive timestamp missing or stale');
 const records=[];
 for(const player of archive.players){
  const id=player?.player_id||player?.playerId;
  if(!id||!Array.isArray(player.games))continue;
  for(const [market,key] of Object.entries(MARKET_VALUES)){
   const games=[];let valid=true;
   for(const game of player.games){
    const eventId=game?.eventId||game?.game_id;
    const playedAt=game?.playedAt||game?.game_date;
    const value=game?.values?.[key];
    if(!eventId||!playedAt||!Number.isFinite(Date.parse(playedAt))||Date.parse(playedAt)>now||typeof value!=='number'||!Number.isFinite(value)||value<0){valid=false;break}
    games.push({eventId:String(eventId),playedAt,verified:true,value});
   }
   if(!valid||games.length<15||new Set(games.map(g=>g.eventId)).size!==games.length)continue;
   records.push({playerId:String(id),providerPlayerId:String(id),league:'NFL',market,period:'Full game',source:'nflverse-stats-player-week',independentlyVerified:true,games});
  }
 }
 return records.length?{status:'VERIFIED_GAME_LOGS',schema_version:1,source:'nflverse-stats-player-week',generated_at:new Date(now).toISOString(),records}:{status:'UNAVAILABLE',reason:'archive lacks stable player IDs, verified event dates or 15 valid games',records:[]};
}
module.exports={bridgeNflverseArchive,MARKET_VALUES};
