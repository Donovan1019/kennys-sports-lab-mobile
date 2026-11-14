/* Pure PFL pricing and parlay risk utilities. No external feed and no fabricated picks. */
(function(root){
'use strict';
function finite(x){return typeof x==='number'&&Number.isFinite(x)}
function probability(x){return finite(x)&&x>=0&&x<=1}
function americanToDecimal(odds){if(!finite(odds)||odds===0||Math.abs(odds)<100)throw Error('Invalid American odds');return odds>0?1+odds/100:1+100/Math.abs(odds)}
function impliedProbability(odds){return 1/americanToDecimal(odds)}
function fairAmerican(p){if(!probability(p)||p===0||p===1)throw Error('Probability must be between zero and one');return p>=.5?-Math.round(100*p/(1-p)):Math.round(100*(1-p)/p)}
function expectedValue(p,odds){if(!probability(p))throw Error('Invalid probability');return p*(americanToDecimal(odds)-1)-(1-p)}
function durationOverProbability(survivalAtThreshold){if(!probability(survivalAtThreshold))throw Error('Invalid survival probability');return survivalAtThreshold}
function auditParlay(legs,opts){opts=opts||{};const errors=[];if(!Array.isArray(legs)||legs.length<2||legs.length>5)return {eligible:false,errors:['Parlay must have 2–5 legs']};
const fights=new Map();let decimal=1,product=1;
legs.forEach((leg,i)=>{const prefix='Leg '+(i+1)+': ';if(!leg||typeof leg.fightId!=='string'||!leg.fightId.trim()){errors.push(prefix+'missing verified fight ID');return}
if(!['ml','total'].includes(leg.market))errors.push(prefix+'unsupported market');
if(!leg.verified||!leg.fresh||!leg.simulated||!leg.calibrated)errors.push(prefix+'unverified or uncalibrated data');
if(!probability(leg.probability)||leg.probability===0||leg.probability===1)errors.push(prefix+'invalid model probability');
try{decimal*=americanToDecimal(leg.odds)}catch(e){errors.push(prefix+e.message)}
if(probability(leg.probability))product*=leg.probability;
const existing=fights.get(leg.fightId)||[];existing.push(leg);fights.set(leg.fightId,existing);
});
for(const [id,group] of fights){if(group.length>1&&!opts.validatedJointDistribution)errors.push('Same-fight legs require a validated joint distribution: '+id)}
if(errors.length)return {eligible:false,errors};
if([...fights.values()].some(group=>group.length>1))return {eligible:false,errors:['Joint distribution input required; independence estimate prohibited']};
if(!opts.crossFightIndependenceValidated)return {eligible:false,errors:['Cross-fight dependence assumptions not validated']};
if(!opts.simulationVerified)return {eligible:false,errors:['Joint parlay Monte Carlo not verified']};
if(!probability(opts.jointProbability))return {eligible:false,errors:['Missing simulated joint probability']};
return {eligible:true,errors:[],decimalOdds:decimal,modelProbability:opts.jointProbability,independenceReference:product,expectedValue:opts.jointProbability*(decimal-1)-(1-opts.jointProbability)};
}
root.KSLPFLMath=Object.freeze({americanToDecimal,impliedProbability,fairAmerican,expectedValue,durationOverProbability,auditParlay});
})(typeof window!=='undefined'?window:globalThis);
