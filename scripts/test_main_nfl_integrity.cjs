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
assert(html.includes('three_sport_player_projections.js?v=20261025-projection-audit-224'),'NFL main cache version not bumped');
const projections=fs.readFileSync('three_sport_player_projections.js','utf8');
assert(projections.includes("sport==='NFL'?{factor:1,verified:false}:opponentFactor(game,p.team)"),'NFL scoring-based projection inflation must remain disabled');
assert(projections.includes("sport==='NFL'?0.25*avg(recent)"),'NFL projection must use conservative history blend');
assert(projections.includes('Number(data[0].season)!==2026'),'Must reject NFL players with stale last-season game histories');
assert(projections.includes('a.every((t,i)=>teamMatch(t,b[i])'),'Must match sportsbook events with canonical team aliases');
console.log('PASS main NFL page, scripts and position/market integrity');
