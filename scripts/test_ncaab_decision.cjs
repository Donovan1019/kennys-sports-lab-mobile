/* Deterministic NCAA market board integrity tests. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('ncaab_decision.js','utf8');
const sandbox={window:{},Date,Intl};vm.runInNewContext(source,sandbox);
const b=sandbox.window.NCAABDecision;
assert.strictEqual(b.etDate('2026-11-11T00:30:00Z'),'2026-11-10');
assert(Math.abs(b.implied(-150)-0.6)<1e-9);
const event={commence_time:'2026-11-11T00:30:00Z',away_team:'Away',home_team:'Home',bookmakers:[{title:'Test Book',markets:[{key:'totals',outcomes:[{name:'Over',point:150.5,price:-110}]}]}]};
const fresh={fetched_at:new Date(Date.now()-60000).toISOString()};
const ok=b.render([event],'2026-11-10',fresh);
assert(ok.includes('Away @ Home')&&ok.includes('150.5')&&ok.includes('52.4% BE'));
assert(b.render([event],'2026-11-11',fresh).includes('0 games'));
assert(b.render([event],'2026-11-10',{fetched_at:'2020-01-01T00:00:00Z'}).includes('UNAVAILABLE'));
console.log('NCAA date, price and stale snapshot integrity tests passed');
