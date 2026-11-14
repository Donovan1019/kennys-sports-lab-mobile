/* Betting-only PFL market qualification. No fabricated bets or unverified model inputs. */
(function(root){'use strict';
function finite(x){return typeof x==='number'&&Number.isFinite(x)}
function assess(m,now=Date.now()){
const errors=[];if(!m||typeof m!=='object')return {eligible:false,errors:['Market missing']};
if(!['ml','total'].includes(m.market))errors.push('Unsupported market');
if(!m.fightId||!m.selection)errors.push('Missing fight or selection');
if(m.market==='total'&&(!finite(m.line)||m.line<=0||!['over','under'].includes(m.side)||m.settlementVerified!==true))errors.push('Total line or settlement rules not verified');
if(m.fightStatus!=='scheduled'||m.boutVerified!==true)errors.push('Fight not confirmed');
if(m.bookVerified!==true||!m.book)errors.push('Sportsbook not verified');
const stamp=Date.parse(m.oddsTimestamp);if(!Number.isFinite(stamp)||stamp>now+300000||now-stamp>2*3600000)errors.push('Odds stale or undated');
if(!m.modelCalibrated||!m.simulationVerified||!Number.isInteger(m.iterations)||m.iterations<50000)errors.push('Calibration or 50k simulation missing');
if(!finite(m.probability)||m.probability<=0||m.probability>=1)errors.push('Model probability unavailable');
if(!finite(m.odds))errors.push('Odds unavailable');
let ev=null,fairOdds=null,implied=null;
if(errors.length===0){try{ev=root.KSLPFLMath.expectedValue(m.probability,m.odds);fairOdds=root.KSLPFLMath.fairAmerican(m.probability);implied=root.KSLPFLMath.impliedProbability(m.odds)}catch(e){errors.push(e.message)}}
return {eligible:errors.length===0,errors,ev,fairOdds,implied,edge:implied===null?null:m.probability-implied,positiveEV:errors.length===0&&ev>0};
}
function rank(markets,now){return (Array.isArray(markets)?markets:[]).map(m=>({market:m,assessment:assess(m,now)})).filter(x=>x.assessment.eligible).sort((a,b)=>b.assessment.ev-a.assessment.ev)}
root.KSLPFLBets=Object.freeze({assess,rank});
})(typeof window!=='undefined'?window:globalThis);
