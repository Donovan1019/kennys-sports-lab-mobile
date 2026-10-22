(()=>{'use strict';
const root=document.getElementById('matchup-location');if(!root)return;
const card=document.createElement('div');card.className='card';card.innerHTML='<h3>Market & prop audit · research queue</h3><p>Ranks saved external-book market rows for inspection. Not recommendations. A green play requires independently verified sportsbook odds, active player, calibrated projection and positive EV.</p><p id="ksl-market-audit-status">Waiting for saved reference markets…</p><div id="ksl-market-audit-list"></div>';root.append(card);
const sport=document.getElementById('sport'),status=document.getElementById('ksl-market-audit-status'),list=document.getElementById('ksl-market-audit-list');

const historyCache={},paths={NBA:'nba_player_stats.json',NFL:'nfl_player_stats.json',NHL:'nhl_player_stats.json'},fields={NBA:['Points','Rebounds','Assists','Threes'],NFL:['Receiving Yards','Rushing Yards','Passing Yards','Receptions'],NHL:['Goals','Assists','Saves']};let watchToken=0;
async function loadHistoricalWatchlist(chosen){
const token=++watchToken,top=document.getElementById('ksl-top-five'),note=document.getElementById('ksl-top-five-note');try{
if(!historyCache[chosen]){const response=await fetch('./feed/'+paths[chosen],{cache:'no-store'});if(!response.ok)throw Error('HTTP '+response.status);const data=await response.json();if(!Array.isArray(data.players))throw Error('Invalid historical player data');historyCache[chosen]=data.players}
if(token!==watchToken||sport.value!==chosen)return;
const candidates=[];for(const p of historyCache[chosen]){if(!p.name||!Array.isArray(p.games))continue;for(const field of fields[chosen]){const games=p.games.filter(g=>g.values&&Object.prototype.hasOwnProperty.call(g.values,field)&&g.values[field]!==null&&g.values[field]!==''&&Number.isFinite(Number(g.values[field]))&&Date.parse(g.date)<Date.now()).sort((a,b)=>Date.parse(b.date)-Date.parse(a.date)).slice(0,10);if(games.length<5)continue;const mean=games.reduce((sum,g)=>sum+Number(g.values[field]),0)/games.length;candidates.push({name:p.name,team:p.team,field,n:games.length,mean})}}
candidates.sort((a,b)=>b.n-a.n||b.mean-a.mean);const selected=[],seen=new Set();for(const p of candidates){if(seen.has(p.name))continue;seen.add(p.name);selected.push(p);if(selected.length===5)break}
top.replaceChildren();for(const p of selected){const li=document.createElement('li');li.style.marginBottom='12px';li.textContent=p.name+(p.team?' ('+p.team+')':'')+' · '+p.field+' · '+p.mean.toFixed(1)+' historical average over '+p.n+' games · NO VERIFIED PROP LINE OR ODDS · RESEARCH ONLY';top.append(li)}
if(!selected.length){const li=document.createElement('li');li.textContent='No qualifying historical player records. No picks available.';top.append(li)}
if(note)note.textContent='0 verified betting plays. Displaying '+selected.length+' historical player research profiles instead (not ranked by hit probability). These are NOT recommended props; lines, availability, calibration and EV remain unverified.';
}catch(e){if(token!==watchToken)return;top.replaceChildren();const li=document.createElement('li');li.textContent='Historical watchlist unavailable: '+e.message+'. No verified plays.';top.append(li);if(note)note.textContent='No verified props or usable historical fallback.'}
}

function render(){
const rows=window.__kslReferenceMarkets?.[sport.value]||[];list.replaceChildren();
const upcoming=(window.__kslMatchupGames||[]).filter(g=>Date.parse(g.commence_time)>Date.now());const ids=new Set(upcoming.map(g=>g.event_id)),events=new Set(upcoming.map(g=>g.event));
const available=rows.filter(x=>(ids.has(x.event_id)||events.has(x.event))&&Date.parse(x.commence_time)>Date.now()&&Number.isFinite(Number(x.price))&&(Number(x.price)<=-100||Number(x.price)>=100));const fresh=available.filter(x=>{const stamp=Date.parse(x.updated_at);return Number.isFinite(stamp)&&Date.now()-stamp>=0&&Date.now()-stamp<6*3600000});
const markets=new Set(available.map(x=>x.market));const props=available.filter(x=>/player|points|rebounds|assists|receptions|yards|shots|saves|goals|threes/i.test(x.market||'')&&!/spread|total|h2h/i.test(x.market||''));
status.textContent=sport.value+' · '+upcoming.length+' future matchups · '+available.length+' matching external market rows · '+fresh.length+' updated within 6 hours · '+props.length+' possible player-prop rows · '+markets.size+' distinct market types. SPORTSBOOK UNVERIFIED.';
const top=document.getElementById('ksl-top-five'),note=document.getElementById('ksl-top-five-note');
if(top){top.replaceChildren();const candidates=(fresh.length?fresh:available).filter(x=>/player|points|rebounds|assists|receptions|yards|shots|saves|goals|threes/i.test(x.market||'')&&!/spread|total|h2h/i.test(x.market||'')).sort((a,b)=>Date.parse(b.updated_at||0)-Date.parse(a.updated_at||0)).slice(0,5);
for(const x of candidates){const li=document.createElement('li');li.style.marginBottom='12px';li.textContent=[x.player||x.selection||x.outcome||'Selection not supplied',x.market,x.point!=null?'Line '+x.point:null,x.price!=null?'Odds '+(x.price>0?'+':'')+x.price:null,x.bookmaker||'Book unknown'].filter(Boolean).join(' · ')+' · '+(fresh.includes(x)?'RECENT EXTERNAL REFERENCE':'STALE REFERENCE')+' · RESEARCH ONLY';top.append(li)}
if(!candidates.length){const li=document.createElement('li');li.textContent='No priced player props in matched sportsbook feeds. Loading historical player research watchlist…';top.append(li);loadHistoricalWatchlist(sport.value)}
if(note)note.textContent='Showing '+candidates.length+' of up to 5 available player-prop candidates. Sorted by source update time, NOT betting quality. None is approved or green until model probability, availability, sportsbook odds and EV are validated.';
}
if(!available.length){list.textContent='No usable future market rows matched this matchup feed. Refresh needed; no green recommendations.';return}if(!fresh.length){const warning=document.createElement('p');warning.className='warn';warning.textContent='ALL MATCHED PRICES STALE OR TIMESTAMP UNKNOWN — no actionable prop shortlist. Refresh sportsbook data before evaluating.';list.append(warning)}
const heading=document.createElement('p');heading.textContent='Research-only market candidates (not sorted by hit probability; no calibrated estimates):';list.append(heading);
for(const x of available.slice(0,15)){const item=document.createElement('p');item.className='pick-pending';item.textContent=[x.event,x.market,x.player||x.selection,x.point,x.price,x.bookmaker].filter(v=>v!==null&&v!==undefined).join(' · ')+' · '+(fresh.includes(x)?'RECENT EXTERNAL REFERENCE':'STALE REFERENCE')+' · SPORTSBOOK UNVERIFIED / NO PLAY';list.append(item)}
}
document.addEventListener('ksl-reference-markets-updated',render);document.getElementById('sport').addEventListener('change',render);
const observer=new MutationObserver(()=>render());const games=document.getElementById('ksl-context-games');observer.observe(games,{childList:true});render();
})();