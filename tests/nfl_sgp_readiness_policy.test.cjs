'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const script=fs.readFileSync('nfl_sgp_readiness_policy.js','utf8');
async function render(quoteTime, kickoff, mutate){
 const panel={textContent:'',children:[],replaceChildren(){this.children=[]},append(x){this.children.push(x)}};
 const fixtures={
  './feed/nfl_sgp_walkforward_accuracy.json':{frozen_forward_holdout:{markets:{player_pass_yds:{eligible_for_live_use:false}}}},
  './feed/player_recommendation_readiness.json':{sports:{NFL:{fully_verified_player_recommendations:0}},source_integrity:{NFL_archived_player_props:{fresh_quotes:0,current_roster_source_connected:false}}},
  './feed/nfl_player_stats.json':{players:[]},
  './feed/nfl_injury_source_health.json':{ingestion_status:'SOURCE_REACHABLE_PARSER_UNAVAILABLE',verified_player_reports:0},
  './feed/nfl_injury_espn_discovery.json':{status:'SCHEMA_DISCOVERED_NOT_VALIDATED',verified_player_reports:0,player_ingestion_enabled:false},
  './feed/nfl_props.json':{odds:['Over','Under'].map(selection=>({event_id:'game',bookmaker:'draftkings',player:'Player',market:'player_pass_yds',point:199.5,selection,updated_at:quoteTime,commence_time:kickoff}))}
 };
 if(mutate)mutate(fixtures);
 const ctx={document:{getElementById:()=>panel,createElement:()=>({textContent:'',style:{},children:[],append(x){this.children.push(x)}})},fetch:async url=>({ok:true,json:async()=>fixtures[url.split('?')[0]]}),Date,Promise};
 vm.runInNewContext(script,ctx);
 await new Promise(resolve=>setImmediate(resolve));
 return panel.children.flatMap(x=>x.children||[]).map(x=>x.textContent);
}
test('fresh exact two-way lines pass quote gates but never unlock bets',async()=>{
 const rows=await render(new Date(Date.now()-60000).toISOString(),new Date(Date.now()+3600000).toISOString());
 assert.ok(rows.some(x=>x.includes('PASS · Fresh DK/FD prop quotes')));
 assert.ok(rows.some(x=>x.includes('PASS · Fresh same-book two-way lines')));
 assert.ok(rows.some(x=>x.includes('BLOCKED · Independent joint SGP calibration')));
 assert.ok(rows.some(x=>x.includes('BLOCKED · Verified injury player reports')));
});
test('stale quotes remain blocked',async()=>{
 const rows=await render(new Date(Date.now()-3600000).toISOString(),new Date(Date.now()+3600000).toISOString());
 assert.ok(rows.some(x=>x.includes('BLOCKED · Fresh DK/FD prop quotes')));
 assert.ok(rows.some(x=>x.includes('BLOCKED · Fresh same-book two-way lines')));
});
test('past kickoff cannot be treated as fresh pregame',async()=>{
 const rows=await render(new Date(Date.now()-60000).toISOString(),new Date(Date.now()-1000).toISOString());
 assert.ok(rows.some(x=>x.includes('BLOCKED · Fresh DK/FD prop quotes')));
});

test('missing player identity cannot create a valid paired line',async()=>{
 const rows=await render(new Date(Date.now()-60000).toISOString(),new Date(Date.now()+3600000).toISOString(),f=>{f['./feed/nfl_props.json'].odds.forEach(q=>{q.player='';q.point=null})});
 assert.ok(rows.some(x=>x.includes('BLOCKED · Fresh same-book two-way lines')));
});
