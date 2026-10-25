#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'grade_nfl_prop_forecasts.cjs'),'utf8');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nfl-prop-grade-'));
try{
 fs.mkdirSync(path.join(dir,'scripts'));fs.mkdirSync(path.join(dir,'feed'));
 fs.writeFileSync(path.join(dir,'scripts','grade_nfl_prop_forecasts.cjs'),source);
 const f={forecast_id:'f1',event_id:'event1',player:'Example Player',market:'Receiving Yards',line:50.5,model_probability:.6,over_odds:-110,under_odds:-110,quoted_at:'2026-10-20T15:00:00Z',forecast_at:'2026-10-20T15:30:00Z',kickoff:'2026-10-20T16:00:00Z',source_repository:'Donovan1019/sports-model-foundation',source_commit:'abc'};
 fs.writeFileSync(path.join(dir,'feed','nfl_prop_forecast_ledger.json'),JSON.stringify({forecasts:[f]}));
 const outcomeFile=path.join(dir,'feed','nfl_prop_verified_outcomes.json');
 const run=()=>cp.spawnSync(process.execPath,[path.join(dir,'scripts','grade_nfl_prop_forecasts.cjs'),outcomeFile],{encoding:'utf8'});
 let a=run();assert.equal(a.status,0);assert.match(a.stdout,/AWAITING_VERIFIED_INPUTS/);
 const o={event_id:'event1',player:'Example Player',market:'Receiving Yards',outcome:64,verified_at:'2026-10-21T03:00:00Z',source:'https://example.com/verified-game-box-score'};
 fs.writeFileSync(outcomeFile,JSON.stringify([o]));
 a=run();assert.equal(a.status,0,a.stderr);
 let graded=JSON.parse(fs.readFileSync(path.join(dir,'feed','nfl_prop_graded_snapshots.json')));assert.equal(graded.length,1);assert.equal(graded[0].outcome,64);
 a=run();assert.equal(a.status,0);graded=JSON.parse(fs.readFileSync(path.join(dir,'feed','nfl_prop_graded_snapshots.json')));assert.equal(graded.length,1);
 fs.writeFileSync(outcomeFile,JSON.stringify([{...o,outcome:63}]));a=run();assert.notEqual(a.status,0,'changed grade must fail');
 fs.writeFileSync(outcomeFile,JSON.stringify([{...o,verified_at:'2026-10-20T15:00:00Z'}]));a=run();assert.notEqual(a.status,0,'premature grading must fail');
 fs.writeFileSync(outcomeFile,JSON.stringify([o,{...o,outcome:63}]));a=run();assert.notEqual(a.status,0,'conflicting duplicate outcomes must fail');
 console.log('PASS: exact NFL prop matching, idempotency and outcome integrity');
}finally{fs.rmSync(dir,{recursive:true,force:true})}
