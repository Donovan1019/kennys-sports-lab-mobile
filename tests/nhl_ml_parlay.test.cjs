// Run: node --test tests/nhl_ml_parlay.test.cjs
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const code=fs.readFileSync('nhl_ml_parlay.js','utf8').replace(/load\(\);\s*$/,'');
const context={Intl,Date,Math,Object,Array,Map,Set,String,Number,document:{getElementById:()=>({})}};vm.createContext(context);vm.runInContext(code,context);
test('ET date conversion does not depend on locale format',()=>assert.equal(vm.runInContext("dateET('2026-11-10T01:10:00Z')",context),'2026-11-09'));
test('American odds decimal conversion',()=>{assert.ok(Math.abs(vm.runInContext('dec(-150)',context)-1.6666666667)<1e-6);assert.equal(vm.runInContext('dec(120)',context),2.2)});
test('Combined American odds positive and negative',()=>{assert.equal(vm.runInContext('parlayOdds(2.5)',context),'+150');assert.equal(vm.runInContext('parlayOdds(1.5)',context),'-200')});
test('ET rollover',()=>assert.equal(vm.runInContext("dateET('2026-11-10T05:10:00Z')",context),'2026-11-10'));
