'use strict';
// Independent ESPN boxscore fallback. ESPN IDs must never be treated as PrizePicks IDs.
const BASE='https://site.api.espn.com/apis/site/v2/sports/basketball/nba/';
const SOURCE='espn-public-boxscore';
const norm=s=>String(s||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
async function json(url,fetcher){const r=await fetcher(url,{signal:AbortSignal.timeout(12000)});if(!r.ok)throw Error('HTTP '+r.status);return r.json()}
function boxscore(data,id,now){
 const c=data?.header?.competitions?.[0],date=Date.parse(c?.date||'');
 if(c?.status?.type?.state!=='post'||!Number.isFinite(date)||date>now)return [];
 const out=[];
 for(const team of data?.boxscore?.players||[])for(const group of team.statistics||[]){
  const labels=group.labels||[];
  for(const row of group.athletes||[]){
   if(row.didNotPlay||!row.athlete?.id)continue;
   const stats={};labels.forEach((k,i)=>{const raw=row.stats?.[i];if(/^\d+-\d+$/.test(String(raw))) {const [a,b]=raw.split('-').map(Number);stats[k+'M']=a;stats[k+'A']=b;}else if(raw!==''&&raw!=null&&Number.isFinite(Number(raw)))stats[k]=Number(raw)});
   out.push({id:String(row.athlete.id),name:row.athlete.displayName,game:String(id),date:new Date(date).toISOString(),stats});
  }
 }
 return out;
}
const FIELDS={Points:'PTS',Rebounds:'REB',Assists:'AST','3-Pointers Made':'3PTM',Steals:'STL',Blocks:'BLK',Turnovers:'TO','Field Goals Made':'FGM','Field Goals Attempted':'FGA','Free Throws Made':'FTM','Free Throws Attempted':'FTA','3-Pointers Attempted':'3PTA','Offensive Rebounds':'OREB','Defensive Rebounds':'DREB'};
function records(rows,feed){
 const names=new Set((feed.lines||[]).filter(x=>x.league==='NBA').map(x=>norm(x.player)));
 const groups=new Map();
 for(const r of rows){const name=norm(r.name);if(!names.has(name))continue;if(!groups.has(name))groups.set(name,new Map());const ids=groups.get(name);if(!ids.has(r.id))ids.set(r.id,[]);ids.get(r.id).push(r)}
 const out=[];
 for(const ids of groups.values()){if(ids.size!==1)continue;const [id,games]=[...ids][0];for(const [market,key] of Object.entries(FIELDS)){const seen=new Set(),valid=[];for(const g of games){const v=g.stats[key];if(!Number.isFinite(v)||v<0||seen.has(g.game))continue;seen.add(g.game);valid.push({eventId:g.game,playedAt:g.date,verified:true,value:v})}if(valid.length<15)continue;valid.sort((a,b)=>a.playedAt.localeCompare(b.playedAt));out.push({playerId:id,providerPlayerId:id,league:'NBA',market,period:'Full game',source:SOURCE,independentlyVerified:true,games:valid})}}
 return out;
}
async function collect(feed,now=Date.now(),fetcher=fetch){
 const diagnostics={days:0,events:0,boxscores:0,failures:[],reason:null},events=new Set(),rows=[];
 // Bounded 90-day backfill; scoreboard requests batched to limit concurrent traffic.
 const days=Array.from({length:35},(_,i)=>new Date(now-(i+1)*86400000));
 const year=new Date(now).getUTCFullYear();
 for(let i=0;i<35;i++)days.push(new Date(Date.UTC(year,3,15)-i*86400000));
 for(let offset=0;offset<days.length;offset+=4){
  const dates=days.slice(offset,offset+4).map(d=>d.toISOString().slice(0,10).replace(/-/g,''));
  const settled=await Promise.allSettled(dates.map(d=>json(BASE+'scoreboard?dates='+d+'&limit=30',fetcher)));
  settled.forEach((r,i)=>{if(r.status==='rejected'){diagnostics.failures.push('scoreboard '+dates[i]+': '+r.reason.message);return}diagnostics.days++;for(const e of r.value.events||[])if(e.status?.type?.state==='post'&&/^\d+$/.test(String(e.id)))events.add(String(e.id))});
 }
 diagnostics.events=events.size;
 const ids=[...events].slice(0,250);
 for(let i=0;i<ids.length;i+=4){const batch=ids.slice(i,i+4);const settled=await Promise.allSettled(batch.map(id=>json(BASE+'summary?event='+id,fetcher)));settled.forEach((r,j)=>{if(r.status==='rejected'){diagnostics.failures.push('summary '+batch[j]+': '+r.reason.message);return}const games=boxscore(r.value,batch[j],now);if(games.length){diagnostics.boxscores++;rows.push(...games)}})}
 const nameIds=new Map();for(const r of rows){const n=norm(r.name);if(!nameIds.has(n))nameIds.set(n,new Set());nameIds.get(n).add(r.id)}
 diagnostics.identityCandidates=[...new Map((feed.lines||[]).filter(x=>x.league==='NBA'&&x.player_id).map(x=>[String(x.player_id),x])).values()].map(line=>({prizepicksPlayerId:String(line.player_id),player:line.player,espnCandidateIds:[...(nameIds.get(norm(line.player))||[])],status:'UNVERIFIED_NAME_CANDIDATE'}));
 const history=records(rows,feed);if(!history.length)diagnostics.reason='No player-market has 15 validated ESPN games';
 return {schema_version:1,status:history.length?'VERIFIED_GAME_LOGS':'UNAVAILABLE',source:SOURCE,generated_at:new Date(now).toISOString(),records:history,diagnostics};
}
module.exports={collect,boxscore,records,SOURCE};
