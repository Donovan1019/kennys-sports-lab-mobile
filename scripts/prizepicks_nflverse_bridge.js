/* Reuse existing nflverse player-game archive, never infer identity or event dates. */
'use strict';
const MARKET_VALUES=Object.freeze({'Passing yards':'Passing yards','Rushing yards':'Rushing yards','Receiving yards':'Receiving yards','Receptions':'Receptions','Passing touchdowns':'Passing touchdowns','Rushing touchdowns':'Rushing touchdowns','Receiving touchdowns':'Receiving touchdowns','Pass Attempts':'Pass Attempts','Pass Completions':'Completions','Rush Attempts':'Rush Attempts'});
function bridgeNflverseArchive(archive,now=Date.now()){
 const fail=reason=>({status:'UNAVAILABLE',reason,records:[]});
 if(!archive)return fail('nflverse archive missing or unreadable');
 if(archive.source!=='nflverse-stats-player-week')return fail('nflverse archive source identifier not recognized');
 if(!Array.isArray(archive.players))return fail('nflverse archive players array missing');
 if(archive.independentlyVerified!==true)return fail('nflverse archive lacks independent verification');
 if(!archive.fetched_at)return fail('nflverse archive fetch timestamp missing');
 const fetched=Date.parse(archive.fetched_at);
 if(!Number.isFinite(fetched)||fetched>now+60000||now-fetched>7*86400000)return fail('nflverse archive timestamp missing or stale');
 const records=[];
 const combinedGames=player=>player.games.map(g=>{
  const a=g?.values?.['Rushing yards'],b=g?.values?.['Receiving yards'];
  const values={...g.values};
  if(typeof a==='number'&&Number.isFinite(a)&&typeof b==='number'&&Number.isFinite(b))values['Rush+Rec Yds']=a+b;
  const attempts=values['Pass Attempts'],completions=values['Completions'],carries=values['Rush Attempts'];
  if(Number.isFinite(attempts)&&attempts>0&&Number.isFinite(completions)&&completions>=0&&completions<=attempts)values['Completion Percentage']=100*completions/attempts;
  if(Number.isFinite(carries)&&carries>0&&Number.isFinite(a))values['Rush Yards Per Carry']=a/carries;
  return {...g,values};
 });
 for(const player of archive.players){
  const id=player?.player_id||player?.playerId;
  if(!id||!Array.isArray(player.games))continue;
  for(const [market,key] of Object.entries({...MARKET_VALUES,'Rush+Rec Yds':'Rush+Rec Yds','Completion Percentage':'Completion Percentage','Rush Yards Per Carry':'Rush Yards Per Carry'})){
   const games=[];let valid=true;
   for(const game of combinedGames(player)){
    const eventId=game?.eventId||game?.game_id;
    const playedAt=game?.playedAt||game?.game_date;
    const value=game?.values?.[key];
    if(value===undefined||value===null)continue;
    if(game?.verified!==true||!eventId||!playedAt||!Number.isFinite(Date.parse(playedAt))||Date.parse(playedAt)>now||typeof value!=='number'||!Number.isFinite(value)||(value<0&&!['Passing yards','Rushing yards','Receiving yards','Rush+Rec Yds','Rush Yards Per Carry'].includes(market))||value< -1000){valid=false;break}
    games.push({eventId:String(eventId),playedAt,verified:true,value});
   }
   if(!valid||games.length<15||new Set(games.map(g=>g.eventId)).size!==games.length)continue;
   games.sort((a,b)=>Date.parse(a.playedAt)-Date.parse(b.playedAt));
   records.push({playerId:String(id),providerPlayerId:String(id),league:'NFL',market,period:'Full game',source:'nflverse-stats-player-week',independentlyVerified:true,games});
  }
 }
 return records.length?{status:'VERIFIED_GAME_LOGS',schema_version:1,source:'nflverse-stats-player-week',generated_at:new Date(now).toISOString(),records}:{status:'UNAVAILABLE',reason:'archive lacks stable player IDs, verified event dates or 15 valid games',records:[]};
}
module.exports={bridgeNflverseArchive,MARKET_VALUES};
