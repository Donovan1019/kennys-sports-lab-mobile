'use strict';
/** Pure mathematical functions; predictions must be independently calibrated before staking. */
function impliedProbability(american){
  if(!Number.isFinite(american)||Math.abs(american)<100)return null;
  return american<0?-american/(-american+100):100/(american+100);
}
function decimalOdds(american){
  if(impliedProbability(american)===null)return null;
  return american<0?1+100/-american:1+american/100;
}
function noVig(a,b){
  const pa=impliedProbability(a),pb=impliedProbability(b);
  if(pa===null||pb===null)return null;
  const sum=pa+pb;
  if(sum<1||sum>1.35)return null;
  return {a:pa/sum,b:pb/sum,overround:sum-1};
}
function expectedValue(probability,american){
  const dec=decimalOdds(american);
  if(!Number.isFinite(probability)||probability<0||probability>1||dec===null)return null;
  return probability*(dec-1)-(1-probability);
}
function kellyFraction(probability,american){
  const dec=decimalOdds(american);
  if(!Number.isFinite(probability)||probability<0||probability>1||dec===null)return null;
  const b=dec-1;
  return Math.max(0,Math.min(1,(b*probability-(1-probability))/b));
}
if(typeof module!=='undefined')module.exports={impliedProbability,decimalOdds,noVig,expectedValue,kellyFraction};
