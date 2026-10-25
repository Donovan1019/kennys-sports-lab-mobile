#!/usr/bin/env node
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('nfl.html','utf8');
assert(html.includes('ksl-stat-root')&&html.includes('ksl-research-root'),'NFL main modules missing');
for(const path of ['three_sport_stats.js','three_sport_player_projections.js']){
 const src=fs.readFileSync(path,'utf8');
 new vm.Script(src,{filename:path});
 assert(src.includes('nflRoles'),'Missing NFL position/market allowlist: '+path);
 assert(src.includes("String(p.position||'').toUpperCase()"),'Missing position validation: '+path);
}
assert(html.includes('three_sport_player_projections.js?v=20261025-bootstrap-228'),'NFL main cache version not bumped');
const projections=fs.readFileSync('three_sport_player_projections.js','utf8');
assert(projections.includes("sport==='NFL'?{factor:1,verified:false}:opponentFactor(game,p.team)"),'NFL scoring-based projection inflation must remain disabled');
assert(projections.includes("sport==='NFL'?0.25*avg(recent)"),'NFL projection must use conservative history blend');
assert(projections.includes('Number(data[0].season)!==2026'),'Must reject NFL players with stale last-season game histories');
assert(projections.includes('a.every((t,i)=>teamMatch(t,b[i])'),'Must match sportsbook events with canonical team aliases');
assert(projections.includes('const simulateProjection='),'NFL projection simulator must be present');
assert(projections.includes('empirical game residual bootstrap'),'NFL simulator must use empirical observations');
assert(html.includes('nfl_all_markets.js?v=20261025-all-markets-231'),'NFL market catalog script missing');
const marketCatalog=fs.readFileSync('nfl_all_markets.js','utf8');new vm.Script(marketCatalog,{filename:'nfl_all_markets.js'});
for(const market of ['h2h','spreads','totals','team_totals','h2h_q1','h2h_q4','totals_q1','totals_q4','team_totals_q4'])assert(marketCatalog.includes(market),'Missing NFL market '+market);
console.log('PASS main NFL page, scripts and position/market integrity');
