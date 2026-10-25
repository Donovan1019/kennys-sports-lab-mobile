#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process'),assert=require('node:assert/strict');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nfl-prop-export-'));
try{
 fs.mkdirSync(path.join(dir,'scripts'));fs.mkdirSync(path.join(dir,'feed'));
 fs.copyFileSync(path.join(__dirname,'export_nfl_prop_forecasts.cjs'),path.join(dir,'scripts','export_nfl_prop_forecasts.cjs'));
 const now=Date.now(),iso=n=>new Date(n).toISOString();
 const q={event_id:'event-1',player:'Sample Player',market:'player_reception_yds',point:45.5,bookmaker:'draftkings',updated_at:iso(now-60000),commence_time:iso(now+3600000)};
 const odds={odds:[{...q,selection:'Over',price:-110},{...q,selection:'Under',price:-110}]};
 const history={players:[{name:'Sample Player',games:Array.from({length:10},(_,i)=>({season:2025,season_type:'REG',values:{'Receiving yards':i%2?65:35}}))}]};
 fs.writeFileSync(path.join(dir,'feed','nfl_props.json'),JSON.stringify(odds));
 fs.writeFileSync(path.join(dir,'feed','nfl_player_stats.json'),JSON.stringify(history));
 const run=()=>cp.spawnSync(process.execPath,[path.join(dir,'scripts','export_nfl_prop_forecasts.cjs')],{encoding:'utf8'});
 let a=run();assert.equal(a.status,0,a.stderr);
 const inbox=path.join(dir,'feed','nfl_prop_forecast_inbox.json');
 let rows=JSON.parse(fs.readFileSync(inbox));assert.equal(rows.length,1);assert.equal(rows[0].model_probability,.5);assert.equal(rows[0].research_only,true);
 fs.writeFileSync(path.join(dir,'feed','nfl_prop_forecast_ledger.json'),JSON.stringify({forecasts:rows}));
 a=run();assert.equal(a.status,0);assert.equal(fs.existsSync(inbox),false,'do not replay stale inbox');
 odds.odds[0].updated_at=iso(now-8*3600000);odds.odds[1].updated_at=iso(now-8*3600000);
 fs.writeFileSync(path.join(dir,'feed','nfl_props.json'),JSON.stringify(odds));
 a=run();assert.equal(a.status,0);assert.equal(fs.existsSync(inbox),false,'stale quotes never generate predictions');
 console.log('PASS: NFL pregame export, deduplication, stale-quote rejection');
}finally{fs.rmSync(dir,{recursive:true,force:true})}
