/* ESPN historical research and possession-quality audit. Not a betting forecast. */
(function(){
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const avg=a=>a.length?a.reduce((x,y)=>x+y,0)/a.length:null;
function render(history,primary){
 if(!history||!Array.isArray(history.games))return '<div class="panel"><h2>ESPN historical research</h2><p>UNAVAILABLE — the first ESPN enrichment workflow must run successfully before historical records appear.</p></div>';
 const rows=history.games,valid=rows.filter(g=>g.teams?.length===2&&g.teams.every(t=>t.possessions_est>35&&t.points!==null));
 const teams=new Map();
 for(const g of valid)for(const t of g.teams){const k=norm(t.name);if(!k)continue;const v=teams.get(k)||{name:t.name,games:0,poss:[],off:[],def:[]};const opponent=g.teams.find(x=>x!==t);v.games++;v.poss.push(t.possessions_est);v.off.push(100*t.points/t.possessions_est);v.def.push(100*opponent.points/opponent.possessions_est);teams.set(k,v)}
 const ranking=[...teams.values()].filter(x=>x.games>=5).sort((a,b)=>b.games-a.games).slice(0,80);
 const table=ranking.map(x=>'<div class="sgp-leg"><span>'+esc(x.name)+' <small>('+x.games+' games)</small></span><span>'+avg(x.poss).toFixed(1)+' poss · '+avg(x.off).toFixed(1)+' ORtg · '+avg(x.def).toFixed(1)+' DRtg</span></div>').join('');
 return '<h2>ESPN historical research</h2><div class="grid"><div class="stat"><small>Completed games cached</small><strong>'+rows.length+'</strong></div><div class="stat"><small>Both teams possession inputs</small><strong>'+valid.length+'</strong></div><div class="stat"><small>Teams with ≥5 usable games</small><strong>'+ranking.length+'</strong></div></div><p class="sgp-note">Possessions estimated as FGA − offensive rebounds + turnovers + 0.44 × FTA. Ratings below are raw, not opponent-adjusted. No forecasts, fair odds, EV or Diamond picks implied.</p>'+(table?'<div class="panel">'+table+'</div>':'<div class="panel">Accumulating usable completed-game boxscores; minimum five games per team required.</div>')+'<p class="meta">Source: ESPN public scoreboard and boxscores · snapshot '+esc(history.fetched_at||'unknown')+'</p>';
}
window.NCAABHistory={render};
})();