#!/usr/bin/env node
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('nfl.html','utf8');
assert(html.includes('ksl-stat-root')&&html.includes('ksl-research-root'),'NFL main modules missing');
for(const path of ['three_sport_stats.js','three_sport_player_projections.js']){
 const src=fs.readFileSync(path,'utf8');
 new vm.Script(src,{filename:path});
 assert(src.includes('nflRoles'),'Missing NFL position/market allowlist: '+path);
 assert(src.includes("String(p.position||'').toUpperCase()"),'Missing position validation: '+path);
}
assert(html.includes('three_sport_player_projections.js?v=20261025-residual-239'),'NFL main cache version not bumped');
const projections=fs.readFileSync('three_sport_player_projections.js','utf8');
assert(projections.includes("sport==='NFL'?{factor:1,verified:false}:opponentFactor(game,p.team)"),'NFL scoring-based projection inflation must remain disabled');
assert(projections.includes("sport==='NFL'?0.25*avg(recent)"),'NFL projection must use conservative history blend');
assert(projections.includes('Number(data[0].season)!==2026'),'Must reject NFL players with stale last-season game histories');
assert(projections.includes('a.every((t,i)=>teamMatch(t,b[i])'),'Must match sportsbook events with canonical team aliases');
assert(projections.includes('const simulateProjection='),'NFL projection simulator must be present');
assert(projections.includes("const residuals=(p.residuals||[]).filter(Number.isFinite)"),'NFL simulator must consume finite signed forecast residuals');
assert(projections.includes('const empirical=residuals.length>=8&&p.folds>=8'),'Residual bootstrap must require sufficient walk-forward folds');
assert(projections.includes('sample=p.projection+deviations[Math.floor(uniform()*deviations.length)]'),'Simulator must resample signed errors around current forecast');
assert(projections.includes('walk-forward residual bootstrap; calibration pending'),'Simulator must disclose residual method and calibration status');
assert(!projections.includes('empirical game residual bootstrap'),'Legacy raw game-deviation simulator must stay removed');
assert(!html.includes('nfl_all_markets.js'),'Unwanted standalone NFL market catalog must stay removed');
assert(html.includes('nfl_game_projections.js?v=20261101-confidence-guard-518'),'Integrated NFL game projections missing or stale cache version');
const gameProjections=fs.readFileSync('nfl_game_projections.js','utf8');new vm.Script(gameProjections,{filename:'nfl_game_projections.js'});
for(const label of ['Moneyline','Spread','Game Total','Team Total','1st quarter','4th quarter','1st half','2nd half','10000'])assert(gameProjections.includes(label),'Missing projection market or simulator '+label);
assert(gameProjections.includes('MutationObserver'),'Async projection panel must receive game projections');
assert(!gameProjections.includes('else root.before(section)'),'Game projections must not render outside player projection panel');
assert(/nfl_module_nav\.js\?v=[^"']+/.test(html),'NFL module navigation missing');
assert(html.includes('id="nfl-full-results"'),'Full results section must be on NFL main page');
const moduleNav=fs.readFileSync('nfl_module_nav.js','utf8');new vm.Script(moduleNav,{filename:'nfl_module_nav.js'});
for(const id of ['nfl-player-projections','nfl-game-projections','ksl-stat-root','ksl-research-root','nfl-full-results'])assert(moduleNav.includes(id),'Missing NFL module navigation destination '+id);
assert(gameProjections.includes('insertBefore(section,playerMarket)'),'Game projections must appear before player market dropdown inside projection panel');
assert(projections.includes('NOT BET ELIGIBLE'),'Uncalibrated NFL projections must not be labeled betting ready');
assert(projections.includes('const matchingQuotes='),'One shared sportsbook matcher required');
assert(projections.includes('const quoteFor=p=>matchingQuotes(p)'),'Projection probabilities must use same quotes as visible lines');
assert(projections.includes('const bookQuote=(p,book)=>matchingQuotes(p)'),'Book display must use strict quote matcher');
assert(projections.includes("if(sport==='NFL')return 'Calibration pending'"),'NFL Gaussian edge must be suppressed');
assert(projections.includes('residuals:errors.slice(0,20)'),'NFL simulation must use walk-forward forecast residuals');
// Pre-kickoff validation guards: a scored game must never contribute to its own forecast.
assert(projections.includes('const older=data.slice(i+1,i+11).map(x=>x.value)'), 'Walk-forward fold must use strictly older observations');
assert(projections.includes('errors.push(data[i].value-pred)'), 'Residuals must retain actual-minus-forecast sign');
assert(projections.includes('const n=10000,draws=[]'), 'Simulator must preserve 10,000 draws');
assert(projections.includes("if(sport==='NFL')return 'Calibration pending'"), 'Uncalibrated NFL probabilities must remain unpublished');
assert(projections.includes("'NOT BET ELIGIBLE'" ) || projections.includes('NOT BET ELIGIBLE'), 'Uncalibrated projections must stay blocked from betting');

assert(gameProjections.includes('Date.parse(x.date)<cutoff'),'NFL game bootstrap must reject post-kickoff scores');
assert(gameProjections.includes('Date.parse(b.date)-Date.parse(a.date)'),'NFL historical games must be sorted newest-first before truncation');
assert(gameProjections.includes('history(away,g.commence_time),hh=history(home,g.commence_time)'),'NFL bootstrap must use event kickoff as historical cutoff');
assert(gameProjections.includes('confidence tier unavailable until walk-forward calibration passes'),'NFL confidence must be withheld until calibrated');
assert(!gameProjections.includes('Model confidence tier: HIGH'),'Uncalibrated high confidence label must be removed');
console.log('PASS main NFL page, scripts and position/market integrity');
