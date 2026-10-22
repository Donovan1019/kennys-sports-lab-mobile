(()=>{'use strict';
const root=document.getElementById('matchup-location');if(!root)return;
const card=document.createElement('div');card.className='card';card.innerHTML='<h3>Market & prop audit · research queue</h3><p>Ranks saved external-book market rows for inspection. Not recommendations. A green play requires independently verified sportsbook odds, active player, calibrated projection and positive EV.</p><p id="ksl-market-audit-status">Waiting for saved reference markets…</p><div id="ksl-market-audit-list"></div>';root.append(card);
const sport=document.getElementById('sport'),status=document.getElementById('ksl-market-audit-status'),list=document.getElementById('ksl-market-audit-list');
function render(){
const rows=window.__kslReferenceMarkets?.[sport.value]||[];list.replaceChildren();
const upcoming=(window.__kslMatchupGames||[]).filter(g=>Date.parse(g.commence_time)>Date.now());const ids=new Set(upcoming.map(g=>g.event_id)),events=new Set(upcoming.map(g=>g.event));
const available=rows.filter(x=>(ids.has(x.event_id)||events.has(x.event))&&Date.parse(x.commence_time)>Date.now()&&Number.isFinite(Number(x.price))&&(Number(x.price)<=-100||Number(x.price)>=100));const fresh=available.filter(x=>{const stamp=Date.parse(x.updated_at);return Number.isFinite(stamp)&&Date.now()-stamp>=0&&Date.now()-stamp<6*3600000});
const markets=new Set(available.map(x=>x.market));const props=available.filter(x=>/player|points|rebounds|assists|receptions|yards|shots|saves|goals|threes/i.test(x.market||'')&&!/spread|total|h2h/i.test(x.market||''));
status.textContent=sport.value+' · '+upcoming.length+' future matchups · '+available.length+' matching external market rows · '+fresh.length+' updated within 6 hours · '+props.length+' possible player-prop rows · '+markets.size+' distinct market types. SPORTSBOOK UNVERIFIED.';
if(!available.length){list.textContent='No usable future market rows matched this matchup feed. Refresh needed; no green recommendations.';return}if(!fresh.length){const warning=document.createElement('p');warning.className='warn';warning.textContent='ALL MATCHED PRICES STALE OR TIMESTAMP UNKNOWN — no actionable prop shortlist. Refresh sportsbook data before evaluating.';list.append(warning)}
const heading=document.createElement('p');heading.textContent='Research-only market candidates (not sorted by hit probability; no calibrated estimates):';list.append(heading);
for(const x of available.slice(0,15)){const item=document.createElement('p');item.className='pick-pending';item.textContent=[x.event,x.market,x.player||x.selection,x.point,x.price,x.bookmaker].filter(v=>v!==null&&v!==undefined).join(' · ')+' · '+(fresh.includes(x)?'RECENT EXTERNAL REFERENCE':'STALE REFERENCE')+' · SPORTSBOOK UNVERIFIED / NO PLAY';list.append(item)}
}
document.addEventListener('ksl-reference-markets-updated',render);document.getElementById('sport').addEventListener('change',render);
const observer=new MutationObserver(()=>render());const games=document.getElementById('ksl-context-games');observer.observe(games,{childList:true});render();
})();