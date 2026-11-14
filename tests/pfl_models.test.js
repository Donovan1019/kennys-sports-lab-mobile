/* Run: node tests/pfl_models.test.js */
const assert=require('node:assert/strict');
require('../pfl_analytics.js');require('../pfl_duration_model.js');
const A=globalThis.KSLPFLMath,D=globalThis.KSLPFLDuration;
assert.equal(A.americanToDecimal(-150),1+100/150);
assert.equal(A.impliedProbability(100),.5);
assert.equal(A.fairAmerican(.6),-150);
assert.ok(Math.abs(A.expectedValue(.6,100)-.2)<1e-12);
assert.equal(A.auditParlay([{fightId:'a',market:'ml',verified:true,fresh:true,simulated:true,calibrated:true,probability:.6,odds:-120},{fightId:'a',market:'total',verified:true,fresh:true,simulated:true,calibrated:true,probability:.6,odds:100}]).eligible,false);
assert.equal(A.auditParlay([{fightId:'a',market:'ml',verified:true,fresh:true,simulated:true,calibrated:true,probability:.6,odds:-120},{fightId:'b',market:'ml',verified:true,fresh:true,simulated:true,calibrated:true,probability:.7,odds:-150}],{crossFightIndependenceValidated:true,simulationVerified:true,jointProbability:.4}).eligible,true);
const config={rounds:3,hazards:[{ko:.1,sub:.1},{ko:.1,sub:.1},{ko:.1,sub:.1}],iterations:50000,seed:42,verified:true,calibrated:true};
assert.ok(Math.abs(D.survival(config).decisionProbability-.512)<1e-12);
assert.deepEqual(D.simulate(config),D.simulate(config));
assert.throws(()=>D.overAtHalfRound(config,2.5),/within-round/);
assert.throws(()=>D.simulate({...config,iterations:100}),/50k/);
assert.throws(()=>D.simulate({...config,verified:false}),/Verified/);
console.log('PFL model unit tests passed');
