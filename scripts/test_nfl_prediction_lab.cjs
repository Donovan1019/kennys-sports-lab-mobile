#!/usr/bin/env node
// Dependency-free predeployment integrity checks for the NFL prediction lab.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('nfl-matchup-lab.html','utf8');
const scripts=['nfl_matchup_advanced.js','nfl_prediction_engine.js'];
for(const file of scripts)new vm.Script(fs.readFileSync(file,'utf8'),{filename:file});
const inline=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]).filter(x=>x.trim());
for(const [i,script] of inline.entries())new vm.Script(script,{filename:'nfl-matchup-lab.html:inline:'+i});
for(const id of ['game','advancedtabs','advancedcontent','nfl-data-health'])assert(html.includes('id="'+id+'"'),'Missing DOM '+id);
for(const file of scripts)assert(html.includes('src="./'+file+'"'),'Missing script '+file);
const game=JSON.parse(fs.readFileSync('feed/americanfootball_nfl.json','utf8'));
const defense=JSON.parse(fs.readFileSync('feed/americanfootball_nfl_defensive_comparison.json','utf8'));
assert(Array.isArray(game.odds)&&game.odds.length>0,'Missing NFL odds feed');
assert(Array.isArray(defense.events)&&defense.events.length>0,'Missing defensive comparison feed');
assert(defense.games_failed===0,'NFL defensive feed still has rejected historical games');
assert(defense.position_coverage&&['qb','rb','wr','te'].every(p=>defense.position_coverage[p]===defense.events.length),'Incomplete NFL positional matchup coverage');
const e=defense.events[0];
for(const position of ['overall','qb','rb','wr','te'])assert(e.matchup_stats?.season?.[position],'Missing position '+position);
const engine=fs.readFileSync('nfl_prediction_engine.js','utf8');
const advanced=fs.readFileSync('nfl_matchup_advanced.js','utf8');
assert(engine.includes("roles[x]?.includes"),'Prediction markets must enforce player position');
assert(engine.includes("const unique=new Set"),'Top 5 must deduplicate markets');
assert(advanced.includes("roleMarkets["),'Research markets must enforce player position');
assert(engine.includes("selected!=='overall'"),'Position tabs must filter predictions');
assert(engine.includes('!x.fresh')&&engine.includes('x.ev<=0'),'Top 5 must reject stale quotes and nonpositive estimated EV');
assert(engine.includes('NO BET')&&engine.includes('RESEARCH ONLY'),'No-quote fallback must not impersonate betting recommendations');
assert(engine.includes('!\u005b\u0027QB\u0027,\u0027RB\u0027,\u0027WR\u0027,\u0027TE\u0027\u005d.includes')||engine.includes("!['QB','RB','WR','TE'].includes"),'Top 5 must require verified player position');
console.log('PASS NFL scripts, DOM controls, DK/FD feed, defensive data and positional categories');
