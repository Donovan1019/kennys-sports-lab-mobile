#!/usr/bin/env node
'use strict';
const fs=require('fs'),assert=require('assert'),vm=require('vm');
const source=fs.readFileSync('scripts/audit_nfl_sgp_research.cjs','utf8');
new vm.Script(source,{filename:'scripts/audit_nfl_sgp_research.cjs'});
assert(source.includes("now-Date.parse(o.updated_at)>30*60000"),'Freshness gate missing');
assert(source.includes("!p.Over||!p.Under"),'Two-way price gate missing');
assert(source.includes("a.player===b.player"),'Same-player duplicate protection missing');
assert(source.includes("trials:2000"),'Simulation trial count missing');
assert(source.includes("betting_eligible:false"),'Research-only flag missing');
assert(source.includes("official_combined_price_available:false"),'Official SGP price blocker missing');
console.log('PASS NFL SGP audit static safety and syntax checks');
