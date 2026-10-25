#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nfl-audit-'));
const audit=path.resolve(__dirname,'audit_nfl_prop_calibration.cjs'),bridge=path.resolve(__dirname,'bridge_nfl_research.cjs');
const base={market:'Receiving Yards',event_id:'g1',kickoff:'2026-10-25T17:00:00Z',quoted_at:'2026-10-25T15:00:00Z',forecast_at:'2026-10-25T16:00:00Z',graded_at:'2026-10-26T00:00:00Z',player:'Example Player',line:50.5,over_odds:-110,under_odds:-110,model_probability:.56,outcome:61,source_repository:'Donovan1019/sports-model-foundation',source_commit:'abc123',forecast_id:'f1'};
const run=(script,rows,output)=>{const input=path.join(dir,'input.json');fs.writeFileSync(input,JSON.stringify(rows));return cp.spawnSync(process.execPath,[script,input,...(output?[output]:[])],{encoding:'utf8'})};
try{
 let r=run(audit,[base]);assert.equal(r.status,0,r.stderr);let report=JSON.parse(r.stdout);assert.equal(report.status,'NOT_BET_ELIGIBLE');assert.equal(report.markets['Receiving Yards'].eligible,false);
 for(const [label,change] of [['future forecast',{forecast_at:'2026-10-25T18:00:00Z'}],['future quote',{quoted_at:'2026-10-25T18:00:00Z'}],['bad odds',{over_odds:-95}],['bad probability',{model_probability:1.2}],['zero vig',{over_odds:110,under_odds:110}]]){
  r=run(audit,[{...base,...change}]);assert.notEqual(r.status,0,label+' must fail');
 }
 r=run(audit,[base,base]);assert.notEqual(r.status,0,'duplicates must fail');
 const output=path.join(dir,'validated.json');
 r=run(bridge,[base],output);assert.equal(r.status,0,r.stderr);assert.equal(JSON.parse(fs.readFileSync(output)).length,1);
 r=run(bridge,[{...base,source_repository:'unknown'}],output);assert.notEqual(r.status,0,'unknown source must fail');
 r=run(bridge,[{...base,forecast_at:'2026-10-25T18:00:00Z'}],output);assert.notEqual(r.status,0,'post-kickoff forecast must fail');
 console.log('PASS: 10 audit and research-bridge safety checks');
}finally{fs.rmSync(dir,{recursive:true,force:true})}
