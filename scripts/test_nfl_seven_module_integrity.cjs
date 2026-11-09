#!/usr/bin/env node
'use strict';
const fs=require('fs'),assert=require('assert');
const read=p=>fs.readFileSync(p,'utf8');
const page=read('nfl.html'),sgp=read('nfl_sgp_stack_finder.js'),qb=read('nfl_qb_unders.js');
const required=['nfl_sgp_stack_finder.js','nfl_sgp_joint_bootstrap.js','nfl_qb_unders.js','nfl_injury_report.js','nfl_full_results.js','nfl_module_nav.js','nfl_full_slate_dashboard.js','nfl_moneyline_tab.js'];
for(const file of required){assert(fs.existsSync(file),'missing module '+file);assert(page.includes(file),'NFL page does not load '+file)}
for(const id of ['nfl-sgp-stack-finder','nfl-qb-unders','nfl-qb-unders-status','nfl-qb-unders-results','nfl-qb-unders-market','nfl-qb-unders-sample','nfl-qb-unders-refresh','nfl-full-results'])assert(page.includes('id="'+id+'"'),'missing NFL UI target '+id);
for(const market of ['Passing Touchdowns','Passing Yards','Rushing Yards','Interceptions','Pass Attempts','Pass Completions','Rush Attempts','Sacks Taken','Completion Percentage','Yards Per Attempt'])assert(qb.includes("'"+market+"'"),'missing QB market '+market);
for(const tier of ['gold','silver','bronze'])assert(sgp.includes("id:'"+tier+"'"),'missing SGP tier '+tier);
assert(sgp.includes('coverageHtml'),'missing full-slate coverage');
assert(sgp.includes('injury_verified!==true'),'injury verification gate removed');
assert(sgp.includes('role_stable!==true'),'role verification gate removed');
assert(sgp.includes('NO_CALIBRATED_JOINT_SIMULATION'),'joint simulation gate removed');
assert(sgp.includes('NO_VERIFIED_COMBINED_SGP_PRICE'),'official SGP price gate removed');
assert(sgp.includes('Date.now()-Date.parse(x.updated_at)<=30*60000'),'quote freshness gate removed');
for(const file of ['nfl_sgp_stack_finder.js','nfl_qb_unders.js','nfl_full_results.js','nfl_injury_report.js','nfl_module_nav.js','nfl_full_slate_dashboard.js'])new Function(read(file));
console.log('PASS: NFL seven-module page wiring, markets, tiers, simulation and injury gates, freshness, JS syntax');
