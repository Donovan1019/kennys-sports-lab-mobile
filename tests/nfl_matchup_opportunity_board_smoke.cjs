/* Offline smoke tests for fail-closed Matchup Opportunity Board. Run: node tests/nfl_matchup_opportunity_board_smoke.cjs */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const script=fs.readFileSync('nfl_matchup_opportunity_board.js','utf8');
const now=Date.now(),iso=(ms)=>new Date(ms).toISOString();
const feeds={
 './feed/americanfootball_nfl_defensive_comparison.json':{generated_at:iso(now),events:[]},
 './feed/americanfootball_nfl.json':{fetched_at:iso(now),odds:[]},
 './feed/nfl_usage_research.json':{generated_at:iso(now),status:'RESEARCH_ONLY',betting_eligible:false,profiles:[]},
 './feed/nfl_injury_reports.json':{status:'UNAVAILABLE',reports:[]},
 './feed/nfl_wr_betting.json':{picks:[]},
 './feed/nfl_injury_source_health.json':{ingestion_status:'SOURCE_REACHABLE_PARSER_UNAVAILABLE',verified_player_reports:0},
 './feed/nfl_wr_ftn_read_breakdown.json':{season:2026,player_weeks:[]}
};
async function run(overrides={},selectedEvent='none'){
 const root={textContent:'',innerHTML:''},selectors={'mx-event':{value:selectedEvent,addEventListener(){}},'mx-window':{value:'season',addEventListener(){}},'mx-position':{value:'wr',addEventListener(){}},'mx-metric':{value:'receptions_allowed',addEventListener(){}}};
 const document={getElementById(id){return id==='mx-opportunity-board'?root:selectors[id]||null}};
 const files={...feeds,...overrides};
 const context={document,Date,console,fetch:async(path)=>({ok:Object.hasOwn(files,path),json:async()=>files[path]})};
 vm.runInNewContext(script,context,{timeout:1000});
 await new Promise(resolve=>setImmediate(resolve));
 return root.textContent||root.innerHTML;
}
(async()=>{
 let output=await run();assert.match(output,/UNAVAILABLE/);assert.match(output,/No upcoming NFL games/);assert.doesNotMatch(output,/betting-ready/i);
 output=await run({'./feed/americanfootball_nfl.json':{fetched_at:iso(now-7*3600000),odds:[]}});assert.match(output,/event feed stale/);
 output=await run({'./feed/nfl_usage_research.json':{generated_at:iso(now),status:'VERIFIED',betting_eligible:true,profiles:[]}});assert.match(output,/eligibility contract/);
 output=await run({'./feed/americanfootball_nfl_defensive_comparison.json':{generated_at:iso(now-49*3600000),events:[]}});assert.match(output,/Defensive snapshot stale/);
 const event={event_id:'test-game',event:'Arizona Cardinals @ Atlanta Falcons',commence_time:iso(now+86400000)};
 const positive={
  './feed/americanfootball_nfl.json':{fetched_at:iso(now),odds:[event]},
  './feed/americanfootball_nfl_defensive_comparison.json':{generated_at:iso(now),events:[{event_id:'test-game',matchup_stats:{season:{wr:{home:{receptions_allowed:{value:9,sample_size:4,games_in_window:4}},away:{receptions_allowed:{value:8,sample_size:4,games_in_window:4}}}}}}]},
  './feed/nfl_usage_research.json':{generated_at:iso(now),status:'RESEARCH_ONLY',betting_eligible:false,profiles:[{nflverse_player_id:'00-001',name:'Test Receiver',team:'ARI',position:'WR',latest_week:9,markets:{}}]}
 };
 output=await run(positive,'test-game');assert.match(output,/Test Receiver/);assert.match(output,/Historical opportunity research/);assert.match(output,/UNVERIFIED/);
 const injury={status:'VERIFIED',reports:[{verified:true,event_id:'other-game',report_type:'official_inactives',source_url:'https://www.nfl.com/injuries/',reported_at:iso(now-120000),fetched_at:iso(now-60000),players:[{name:'Test Receiver',team:'Arizona Cardinals',status:'inactive'}]}]};
 output=await run({...positive,'./feed/nfl_injury_reports.json':injury},'test-game');assert.doesNotMatch(output,/OUT \/ INACTIVE/);
 injury.reports[0].event_id='test-game';
 output=await run({...positive,'./feed/nfl_injury_reports.json':injury},'test-game');assert.match(output,/OUT \/ INACTIVE/);
 console.log('PASS: empty slate, stale event, invalid usage eligibility, stale defense, matched matchup, cross-game injury isolation, inactive flag');
})().catch(e=>{console.error(e);process.exitCode=1});
