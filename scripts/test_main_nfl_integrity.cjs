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
assert(html.includes('20261025-source-debug'),'NFL main cache version not bumped');
console.log('PASS main NFL page, scripts and position/market integrity');
