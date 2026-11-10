/* Research-only NCAA possession and coverage engine. No calibrated probabilities. */
(function(){
'use strict';
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const avg=a=>a.length?a.reduce((x,y)=>x+y,0)/a.length:null;
function analyze(history,primary){
 const games=history?.games||[],teams=new Map(),seen=new Set();
 for(const g of games){
  if(seen.has(g.event_id)||g.teams?.length!==2)continue;seen.add(g.event_id);
  if(!g.teams.every(t=>t.possessions_est>35&&Number.isFinite(t.points)))continue;
  for(const t of g.teams){
   const opponent=g.teams.find(x=>x!==t),key=norm(t.name);
   if(!key)continue;
   const row=teams.get(key)||{name:t.name,n:0,pace:[],off:[],def:[],latest:null};
   row.n++;row.pace.push((t.possessions_est+opponent.possessions_est)/2);
   row.off.push(100*t.points/t.possessions_est);
   row.def.push(100*opponent.points/opponent.possessions_est);
   if(!row.latest||g.date>row.latest)row.latest=g.date;
   teams.set(key,row);
  }
 }
 const eligible=[...teams.values()].filter(x=>x.n>=5).map(x=>({name:x.name,n:x.n,pace:avg(x.pace),off:avg(x.off),def:avg(x.def),latest:x.latest}));
 const coverage={games:games.length,possessions:seen.size,teams:teams.size,eligible:eligible.length,ready:false,reason:'No point-in-time calibrated model or verified player-prop odds'};
 return {coverage,teams:eligible};
}
function render(history,primary){
 if(!history)return '<div class="panel">UNAVAILABLE — ESPN historical data has not been populated.</div>';
 const result=analyze(history,primary),c=result.coverage;
 return '<h2>Model Quality & Coverage</h2><div class="grid"><div class="stat"><small>Cached games</small><strong>'+c.games+'</strong></div><div class="stat"><small>Teams observed</small><strong>'+c.teams+'</strong></div><div class="stat"><small>Teams with 5+ games</small><strong>'+c.eligible+'</strong></div></div><div class="panel"><strong>RESEARCH ONLY — NOT BETTING READY</strong><p>Raw estimated pace and efficiency are descriptive. No opponent adjustment, validated home advantage, backtested win/cover/total probabilities, player-prop distribution, correlated SGP quote or EV claim is available.</p></div>'+result.teams.slice(0,100).map(t=>'<div class="sgp-leg"><span>'+esc(t.name)+' ('+t.n+')</span><span>'+t.pace.toFixed(1)+' poss · '+t.off.toFixed(1)+' ORtg · '+t.def.toFixed(1)+' DRtg</span></div>').join('')+'<p class="sgp-note">Coverage gate: '+esc(c.reason)+'</p>';
}
window.NCAABQuality={analyze,render};
})();