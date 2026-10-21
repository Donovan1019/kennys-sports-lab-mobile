/* Visible, independent top-of-page player research for NFL, NBA, NHL. */
(()=>{'use strict';
const main=document.querySelector('main');if(!main)return;
const sports=['NFL','NBA','NHL'];
const config={NFL:{feed:'nfl_props.json'},NBA:{feed:'nba_player_stats.json',metric:'Points'},NHL:{feed:'nhl_official_player_stats.json',metric:'Shots on goal'}};
for(const sport of sports){
 const root=document.createElement('section');root.id='ksl-'+sport.toLowerCase()+'-top-players';root.className='ksl-top-players';
 root.style.cssText='border:2px solid #4ca96d;border-radius:14px;padding:16px;margin:12px 0 16px;background:#10221d;color:#ecfff0';
 const title=document.createElement('h2');title.textContent=sport+' · Top Players Research';root.append(title);
 const note=document.createElement('p');note.textContent='Historical evidence only. Not a list of verified betting plays or live sportsbook lines.';root.append(note);
 const state=document.createElement('p');state.textContent='Loading player research…';state.setAttribute('role','status');root.append(state);
 const list=document.createElement('div');root.append(list);
 main.prepend(root);
 (async()=>{
 try{
  const response=await fetch('./feed/'+config[sport].feed,{cache:'no-store'});if(!response.ok)throw Error('Feed unavailable');
  const data=await response.json();let rows=[];
  if(sport==='NFL'){
   const byPlayer=new Map();
   for(const q of data.odds||[]){if(!q.player||!q.market)continue;const key=q.player;const record=byPlayer.get(key)||{name:key,markets:new Set(),quotes:0};record.markets.add(q.market);record.quotes++;byPlayer.set(key,record);}
   rows=[...byPlayer.values()].sort((a,b)=>b.markets.size-a.markets.size||b.quotes-a.quotes||a.name.localeCompare(b.name)).slice(0,10).map(p=>({name:p.name,detail:p.markets.size+' archived market types · '+p.quotes+' quotes'}));
   state.textContent=rows.length?'Archived NFL player market coverage · '+(data.fetched_at||'unknown snapshot'):'No archived NFL player quotes available.';
  }else{
   const metric=config[sport].metric;
   rows=(data.players||[]).map(p=>{const games=(p.games||[]).filter(g=>Number.isFinite(g.values?.[metric])&&!(g.quality_flags||[]).length).sort((a,b)=>String(b.date).localeCompare(String(a.date))).slice(0,5);return {name:p.name+' ('+(p.team||'team unknown')+')',games,avg:games.length?games.reduce((v,g)=>v+g.values[metric],0)/games.length:0};}).filter(p=>p.games.length>=3).sort((a,b)=>b.avg-a.avg).slice(0,10).map(p=>({name:p.name,detail:p.avg.toFixed(2)+' '+metric+'/game · last '+p.games.length+' recorded games'}));
   state.textContent=rows.length?'Top recorded '+metric+' averages · '+(data.fetched_at||'unknown snapshot'):'No qualifying player history yet. Feed collection may still be pending.';
  }
  for(const [i,p] of rows.entries()){const line=document.createElement('div');line.style.cssText='border-top:1px solid #365e49;padding:10px 0';const strong=document.createElement('strong');strong.textContent=(i+1)+'. '+p.name;const detail=document.createElement('div');detail.textContent=p.detail;detail.style.cssText='font-size:13px;color:#b7d3bf';line.append(strong,detail);list.append(line);}
 }catch(err){state.textContent='Player research unavailable; no results invented.';}
 })();
}
})();