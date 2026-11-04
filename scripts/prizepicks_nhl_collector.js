/* Official NHL game logs. Roster names select candidates only; they NEVER verify PrizePicks IDs. */
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const TEAMS='ANA BOS BUF CAR CBJ CGY CHI COL DAL DET EDM FLA LAK MIN MTL NJD NSH NYI NYR OTT PHI PIT SEA SJS STL TBL TOR UTA VAN VGK WPG WSH'.split(' ');
const SOURCE='api-web.nhle.com/v1';
function seasonId(now=new Date()){const y=now.getUTCFullYear()-(now.getUTCMonth()<8?1:0);return String(y)+String(y+1)}
function cleanName(v){return String(v||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'')}
async function getJson(url,fetcher=fetch,wait=ms=>new Promise(resolve=>setTimeout(resolve,ms))){
 for(let attempt=0;attempt<3;attempt++){
  try{
   const res=await fetcher(url,{headers:{accept:'application/json'},signal:AbortSignal.timeout(12000)});
   if(res.ok)return await res.json();
   if(![429,500,502,503,504].includes(res.status)||attempt===2)throw Error('NHL HTTP '+res.status);
  }catch(e){if(attempt===2||/^NHL HTTP (?!429|50[0234])/.test(e.message))throw e}
  await wait(250*Math.pow(2,attempt));
 }
 throw Error('NHL retry exhausted');
}
function convertLog(id,log,now=Date.now()){
 const fields={'Shots on Goal':'shots','Goals':'goals','Assists':'assists','Points':'points','Blocked Shots':'blockedShots'};
 const records=[];
 for(const [market,field] of Object.entries(fields)){
  const games=[];
  for(const g of log){
   const v=g?.[field],date=g?.gameDate,gameId=g?.gameId;
   if(!Number.isInteger(gameId)&&typeof gameId!=='string')continue;
   if(!/^\d{4}-\d{2}-\d{2}$/.test(String(date||'')))continue;
   const played=Date.parse(date+'T12:00:00Z');
   if(!Number.isFinite(played)||played>now||!Number.isFinite(v)||v<0)continue;
   games.push({eventId:String(gameId),playedAt:date+'T12:00:00Z',verified:true,value:v});
  }
  if(games.length<15||new Set(games.map(g=>g.eventId)).size!==games.length)continue;
  games.sort((a,b)=>Date.parse(a.playedAt)-Date.parse(b.playedAt));
  records.push({playerId:String(id),providerPlayerId:String(id),league:'NHL',market,period:'Full game',source:SOURCE,independentlyVerified:true,games});
 }
 return records;
}
async function batches(items,limit,fn){for(let i=0;i<items.length;i+=limit)await Promise.all(items.slice(i,i+limit).map(fn))}
async function collect(feed,now=Date.now(),fetcher=fetch){
 const names=new Set((feed?.lines||[]).filter(x=>x.league==='NHL'&&x.player).map(x=>cleanName(x.player)));
 const output={schema_version:1,status:'UNAVAILABLE',source:SOURCE,generated_at:new Date(now).toISOString(),records:[],diagnostics:{candidateNames:names.size,rosterFailures:[],gameLogFailures:[],matchedRosterIds:0,ambiguousRosterNames:[],verifiedMarketRecords:0,reason:null}};
 if(!names.size){output.diagnostics.reason='no NHL candidate names in source feed';return output}
 const idsByName=new Map();
 await batches(TEAMS,6,async team=>{
  try{
   const roster=await getJson('https://api-web.nhle.com/v1/roster/'+team+'/current',fetcher);
   for(const p of [...(roster.forwards||[]),...(roster.defensemen||[])]){
    const full=[p.firstName?.default,p.lastName?.default].filter(Boolean).join(' ');
    if(names.has(cleanName(full))&&Number.isInteger(p.id)){
     const key=cleanName(full);
     if(!idsByName.has(key))idsByName.set(key,new Set());
     idsByName.get(key).add(p.id);
    }
   }
  }catch(e){output.diagnostics.rosterFailures.push(team+': '+e.message)}
 });
 if(output.diagnostics.rosterFailures.length){
  output.diagnostics.reason='incomplete league roster coverage prevents unique identity verification';
  return output;
 }
 const ids=new Set();
 for(const [name,matches] of idsByName){
  if(matches.size!==1){output.diagnostics.ambiguousRosterNames.push(name);continue}
  ids.add([...matches][0]);
 }
 output.diagnostics.matchedRosterIds=ids.size;
 const season=seasonId(new Date(now));
 const previous=String(Number(season.slice(0,4))-1)+String(Number(season.slice(4))-1);
 await batches([...ids],6,async id=>{
  try{
   const logs=[];
   for(const year of [season,previous]){
    try{
     const data=await getJson('https://api-web.nhle.com/v1/player/'+id+'/game-log/'+year+'/2',fetcher);
     if(!Array.isArray(data.gameLog))throw Error('gameLog array missing');
     logs.push(...data.gameLog);
    }catch(e){output.diagnostics.gameLogFailures.push(String(id)+' '+year+': '+e.message)}
   }
   output.records.push(...convertLog(id,logs,now));
  }catch(e){output.diagnostics.gameLogFailures.push(String(id)+': '+e.message)}
 });
 output.diagnostics.verifiedMarketRecords=output.records.length;
 if(output.records.length)output.status='VERIFIED_GAME_LOGS';
 else output.diagnostics.reason=output.diagnostics.matchedRosterIds?'no NHL player has 15 distinct verified games per market':'no unambiguous NHL roster matches';
 return output;
}
async function main(){
 const feed=JSON.parse(fs.readFileSync(process.env.PRIZEPICKS_FEED_PATH||'feed/prizepicks_lines.json','utf8'));
 const result=await collect(feed);
 const dest=process.env.PRIZEPICKS_NHL_HISTORY_PATH||'feed/prizepicks_nhl_verified_history.json';
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:result.status,records:result.records.length,diagnostics:result.diagnostics}));
}
if(require.main===module)main().catch(e=>{console.error(e);process.exitCode=1});
module.exports={collect,convertLog,seasonId,cleanName,getJson};
