#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'archive_nfl_prop_forecasts.cjs'),'utf8');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nfl-prop-archive-'));
try{
 fs.mkdirSync(path.join(dir,'scripts'));fs.mkdirSync(path.join(dir,'feed'));
 fs.writeFileSync(path.join(dir,'scripts','archive_nfl_prop_forecasts.cjs'),source);
 const now=Date.now(),iso=x=>new Date(x).toISOString();
 const base={forecast_id:'test-1',event_id:'event-1',player:'Example Player',market:'Receiving Yards',line:50.5,model_probability:0.56,over_odds:-110,under_odds:-110,quoted_at:iso(now-120000),forecast_at:iso(now-60000),kickoff:iso(now+3600000),source_commit:'abc123',source_repository:'Donovan1019/sports-model-foundation'};
 const run=rows=>{const file=path.join(dir,'input.json');fs.writeFileSync(file,JSON.stringify(rows));return cp.spawnSync(process.execPath,[path.join(dir,'scripts','archive_nfl_prop_forecasts.cjs'),file],{encoding:'utf8'})};
 assert.equal(run([base]).status,0,'valid pregame forecast must archive');
 assert.equal(run([base]).status,0,'idempotent re-import must pass');
 const ledger=JSON.parse(fs.readFileSync(path.join(dir,'feed','nfl_prop_forecast_ledger.json')));
 assert.equal(ledger.forecasts.length,1,'idempotent archive has one forecast');
 for(const [label,change] of [['conflict',{model_probability:.65}],['future forecast',{forecast_at:iso(now+120000)}],['postkickoff',{kickoff:iso(now-1000)}],['future quote',{quoted_at:iso(now)}],['stale quote',{quoted_at:iso(now-8*3600000)}],['bad odds',{over_odds:-95}],['unknown market',{market:'unknown'}],['no vig',{over_odds:110,under_odds:110}],['unknown provenance',{source_repository:'unknown'}]]){
  const out=run([{...base,...change}]);assert.notEqual(out.status,0,label+' must be rejected');
 }
 const past={...base,forecast_id:'past-1',forecast_at:'2026-10-01T14:00:00Z',quoted_at:'2026-10-01T13:55:00Z',kickoff:'2026-10-01T17:00:00Z'};
 const archivePath=path.join(dir,'feed','nfl_prop_forecast_ledger.json');
 const saved=JSON.parse(fs.readFileSync(archivePath,'utf8'));saved.forecasts.push(past);fs.writeFileSync(archivePath,JSON.stringify(saved));
 assert.equal(run([past]).status,0,'exact replay of archived past kickoff forecast must pass');
 assert.notEqual(run([{...past,model_probability:.71}]).status,0,'changed past kickoff forecast must fail');
 console.log('PASS: NFL prop immutable archive, past-kickoff replay and rejection cases');
}finally{fs.rmSync(dir,{recursive:true,force:true})}
