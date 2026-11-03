/* Independent historical evidence gate: never turns unverified game logs into betting picks. */
'use strict';
function finite(n){return typeof n==='number'&&Number.isFinite(n)}
function historyEvidence(record,line,at=Date.now()){
 const fail=reason=>({status:'UNAVAILABLE',reason});
 if(!record||!finite(line)||line<0)return fail('invalid record or line');
 if(record.independentlyVerified!==true||record.playerId==null||!record.market||!record.league)return fail('independent provenance and player/market identity required');
 if(!Array.isArray(record.games)||record.games.length<15)return fail('at least 15 verified game results required');
 const seen=new Set(),values=[];
 for(const g of record.games){const t=Date.parse(g?.playedAt||'');if(!g||g.verified!==true||!g.eventId||seen.has(g.eventId)||!finite(t)||t>at||!finite(g.value)||g.value<0)return fail('invalid, duplicate, future or unverified game');seen.add(g.eventId);values.push(g.value)}
 const more=values.filter(v=>v>line).length,less=values.filter(v=>v<line).length,push=values.length-more-less;
 const mean=values.reduce((a,b)=>a+b,0)/values.length;
 return {status:'HISTORICAL_ONLY',sample:values.length,more,less,push,moreRate:more/values.length,lessRate:less/values.length,pushRate:push/values.length,mean,modelValidated:false,betEligible:false,source:record.source||'independently verified game logs'};
}
module.exports={historyEvidence};
