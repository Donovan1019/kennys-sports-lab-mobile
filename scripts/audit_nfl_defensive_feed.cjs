#!/usr/bin/env node
// Audits NFL defensive matchup ingestion without masking rejected games.
const fs=require('node:fs');
const feed=JSON.parse(fs.readFileSync('feed/americanfootball_nfl_defensive_comparison.json','utf8'));
const errors=Array.isArray(feed.errors)?feed.errors:[];
const events=Array.isArray(feed.events)?feed.events:[];
const failures=[];
if(!Number.isInteger(feed.games_failed)||feed.games_failed!==errors.length)failures.push('games_failed does not match errors[] length');
for(const e of errors){
 const id=String(e.event_id||'unknown');
 const detail=String(e.detail||'');
 console.error('[REJECTED]',id,e.reason||'unknown',detail);
 if(!detail)failures.push(id+': missing rejection details');
}
for(const pos of ['qb','rb','wr','te']){
 const observed=events.filter(e=>e.matchup_stats?.season?.[pos]).length;
 const declared=feed.position_coverage?.[pos];
 console.log(pos+': '+observed+'/'+events.length+' event records (declared '+declared+')');
 if(declared!==observed)failures.push(pos+': coverage metadata mismatch');
}
for(const e of events){
 for(const [windowName,window] of Object.entries(e.matchup_stats||{})){
  for(const [position,bySide] of Object.entries(window||{})){
   if(!bySide||typeof bySide!=='object')continue;
   for(const side of ['home','away']){
    for(const [metric,value] of Object.entries(bySide[side]||{})){
     if(!value||typeof value!=='object'||!('value' in value))continue;
     if(!Number.isFinite(Number(value.value))||!Number.isInteger(value.sample_size)||value.sample_size<1)
      failures.push(e.event_id+': invalid '+windowName+'/'+position+'/'+side+'/'+metric);
    }
   }
  }
 }
}
console.log('Defensive feed:',feed.generated_at,'scanned',feed.games_scanned,'accepted matchup events',events.length,'rejected',errors.length);
if(errors.length)failures.push(errors.length+' rejected source games require upstream repair');
if(failures.length){console.error('AUDIT FAILED:',failures.join('; '));process.exitCode=1}
else console.log('PASS defensive feed audit');
