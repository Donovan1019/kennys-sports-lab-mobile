/* PFL independent round-duration research engine.
   Input: verified per-round conditional finish hazards, not historical hit-rate guesses.
   No live feed is bundled. */
(function(root){
'use strict';
function checkNumber(v){return typeof v==='number'&&Number.isFinite(v)&&v>=0&&v<=1}
function validate(config){
if(!config||![3,5].includes(config.rounds))throw Error('Scheduled rounds must be 3 or 5');
if(!Array.isArray(config.hazards)||config.hazards.length!==config.rounds)throw Error('One hazard per scheduled round required');
config.hazards.forEach((h,i)=>{if(!h||!checkNumber(h.ko)||!checkNumber(h.sub)||h.ko+h.sub>1)throw Error('Invalid finish hazards in round '+(i+1))});
if(!Number.isInteger(config.seed)||!Number.isInteger(config.iterations)||config.iterations<50000)throw Error('Seeded >=50k simulations required');
if(config.verified!==true||config.calibrated!==true)throw Error('Verified, calibrated fighter inputs required');
}
function rng(seed){let state=seed>>>0;return function(){state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296}}
function survival(config){validate(config);let s=1;const ends=[];config.hazards.forEach((h,i)=>{const before=s;s*=1-h.ko-h.sub;ends.push({round:i+1,startSurvival:before,endSurvival:s,finishProbability:before-s})});return {rounds:ends,decisionProbability:s}}
function simulate(config){
validate(config);const random=rng(config.seed),counts=Array(config.rounds).fill(0),finishTypes={ko:0,sub:0,decision:0};
for(let n=0;n<config.iterations;n++){let outcome='decision';for(let r=0;r<config.rounds;r++){const h=config.hazards[r],u=random();if(u<h.ko){outcome='ko';counts[r]++;break}if(u<h.ko+h.sub){outcome='sub';counts[r]++;break}}finishTypes[outcome]++}
return {iterations:config.iterations,seed:config.seed,finishByRound:counts.map(x=>x/config.iterations),methods:Object.fromEntries(Object.entries(finishTypes).map(([k,v])=>[k,v/config.iterations]))};
}
function overAtHalfRound(config,line){validate(config);if(!Number.isFinite(line)||line%1!==.5||line<0||line>=config.rounds)throw Error('Invalid half-round total');
const completed=Math.floor(line),surv=survival(config).rounds;
if(completed===0)throw Error('Intra-round timing model required');
throw Error('Half-round settlement requires verified within-round finish timing; round-level hazards alone are insufficient');
}
root.KSLPFLDuration=Object.freeze({validate,survival,simulate,overAtHalfRound});
})(typeof window!=='undefined'?window:globalThis);
