/* PFL source confidence and market-value scoring. Research only; never fabricates inputs. */
(function(root){'use strict';
const required=['identity','bout','opponents','results','timing','odds','news'];
function assess(input){const reasons=[];if(!input||typeof input!=='object')return {eligible:false,score:0,grade:'UNAVAILABLE',reasons:['No source evidence']};
let weighted=0,total=0;const weights={identity:20,bout:20,opponents:10,results:15,timing:10,odds:15,news:10};
for(const key of required){const item=input[key],weight=weights[key];total+=weight;
if(!item||item.verified!==true||!Number.isFinite(item.ageHours)||item.ageHours<0){reasons.push(key+': not verified');continue}
const maxAge=key==='odds'?2:key==='news'?24:key==='bout'?24:24*30;
if(item.ageHours>maxAge){reasons.push(key+': stale');continue}weighted+=weight;
}
const score=Math.round(100*weighted/total);
const eligible=score===100&&input.modelCalibrated===true&&input.simulationVerified===true;
if(input.modelCalibrated!==true)reasons.push('Model calibration unavailable');
if(input.simulationVerified!==true)reasons.push('Simulation unavailable');
return {eligible,score,grade:eligible?'COMPLETE':score>=70?'UNVERIFIED':'UNAVAILABLE',reasons};
}
function rankMarkets(markets){if(!Array.isArray(markets))return [];
return markets.map(m=>{const confidence=assess(m.sources);let ev=null;
if(confidence.eligible&&root.KSLPFLMath&&typeof m.probability==='number'&&Number.isFinite(m.odds)){
try{ev=root.KSLPFLMath.expectedValue(m.probability,m.odds)}catch(_){}}
return {...m,confidence,ev,betEligible:confidence.eligible&&ev!==null&&ev>0};
}).sort((a,b)=>Number(b.betEligible)-Number(a.betEligible)||(b.ev??-Infinity)-(a.ev??-Infinity));
}
root.KSLPFLConfidence=Object.freeze({assess,rankMarkets});
})(typeof window!=='undefined'?window:globalThis);
