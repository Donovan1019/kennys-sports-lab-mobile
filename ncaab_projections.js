/* NCAA provisional score projections from verified historical team efficiencies. */
(function(){
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const canonical=s=>norm(String(s||'').replace(/\bSt\.?\b/gi,'State').replace(/\bUConn\b/gi,'Connecticut'));
function project(home,away){
 const pace=(home.pace+away.pace)/2;
 const h=pace*(home.off+away.def)/200;
 const a=pace*(away.off+home.def)/200;
 return {home:h,away:a,total:h+a,margin:h-a};
}
function render(data,events,date){
 const coverage=data?.coverage||{};
 if(!data?.research_only||!coverage.teams)return '<div class="panel">UNAVAILABLE — NCAA research team feed has not been generated yet.</div>';
 const age=Date.now()-Date.parse(data.source_fetched_at||'');
 if(!Number.isFinite(age)||age<0||age>72*3600000)return '<div class="panel">UNAVAILABLE — historical projection feed is older than 72 hours or has no valid timestamp.</div>';
 const teams=Object.values(coverage.teams);
 const progress=Object.values(coverage.team_progress||{});
 const summary='<div class="panel"><strong>'+esc(coverage.eligible_teams??teams.length)+' / '+esc(coverage.observed_teams??progress.length)+' teams eligible</strong><p>Minimum '+esc(coverage.minimum_games||5)+' completed current-season games per team. Data collection is automatic.</p></div>';
 const match=name=>{const hits=teams.filter(t=>canonical(t.team)===canonical(name));return hits.length===1?hits[0]:null};
 const day=events.filter(e=>{const d=new Date(e.commence_time);if(!Number.isFinite(d.getTime()))return false;const p=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(d).split('/');return p[2]+'-'+p[0]+'-'+p[1]===date});
 return '<h2>NCAA Score Projections · Research</h2>'+summary+'<div class="panel"><strong>UNADJUSTED · NOT BETTING-READY</strong><p>Team identities must match exactly. Five completed games per team required. These are raw pace/efficiency estimates, not calibrated win probabilities, fair odds, or EV.</p></div>'+(day.length?day.map(e=>{
 const home=match(e.home_team),away=match(e.away_team);
 if(!home||!away){const progressFor=name=>{const hits=progress.filter(t=>canonical(t.team)===canonical(name));return hits.length===1?esc(hits[0].games)+'/'+esc(coverage.minimum_games||5)+' completed games':'identity/history unavailable'};return '<article class="game"><strong>'+esc(e.away_team)+' @ '+esc(e.home_team)+'</strong><div class="meta">UNAVAILABLE — '+esc(e.away_team)+': '+progressFor(e.away_team)+' · '+esc(e.home_team)+': '+progressFor(e.home_team)+'</div></article>';}
 const p=project(home,away);
 return '<article class="game"><strong>'+esc(e.away_team)+' @ '+esc(e.home_team)+'</strong><div class="grid"><div class="stat"><small>'+esc(e.away_team)+'</small><strong>'+p.away.toFixed(1)+'</strong></div><div class="stat"><small>'+esc(e.home_team)+'</small><strong>'+p.home.toFixed(1)+'</strong></div><div class="stat"><small>Projected total</small><strong>'+p.total.toFixed(1)+'</strong></div><div class="stat"><small>Home margin</small><strong>'+p.margin.toFixed(1)+'</strong></div></div><div class="meta">Research only · '+home.games+' home-team games · '+away.games+' away-team games · no probability or EV</div></article>';
 }).join(''):'<div class="panel">No sportsbook schedule available for the selected date.</div>');
}
window.NCAABProjections={render,project};
})();
