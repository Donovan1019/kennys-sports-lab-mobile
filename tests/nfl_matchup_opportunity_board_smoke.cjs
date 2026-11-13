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
async function run(overrides={}){
 const root={textContent:'',innerHTML:''},selectors={'mx-event':{value:'none',addEventListener(){}},'mx-window':{value:'season',addEventListener(){}},'mx-position':{value:'wr',addEventListener(){}},'mx-metric':{value:'receptions_allowed',addEventListener(){}}};
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
 console.log('PASS: empty slate, stale event, invalid usage eligibility, stale defense');
})().catch(e=>{console.error(e);process.exitCode=1});
