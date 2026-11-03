/* Historical research only. Require verified, unique, point-in-time game logs. */
'use strict';
function finite(n){return typeof n==='number'&&Number.isFinite(n)}
function historyEvidence(record,line,at=Date.now()){
 const fail=reason=>({status:'UNAVAILABLE',reason});
 if(!record||!finite(line)||line<0||!finite(at))return fail('invalid record, line or timestamp');
 if(record.independentlyVerified!==true||!record.playerId||!record.market||!record.league )return fail('independent provenance and player/market identity required');
 if(!Array.isArray(record.games)||record.games.length<15)return fail('at least 15 verified game results required');
 const seen=new Set(),games=[];
 for(const g of record.games){
  const t=Date.parse(g?.playedAt||'');
  if(!g||g.verified!==true||!g.eventId||seen.has(g.eventId)||!Number.isFinite(t)||t>at||!finite(g.value)||g.value<0)return fail('invalid, duplicate, future or unverified game');
  seen.add(g.eventId);games.push({t,value:g.value,id:String(g.eventId)});
 }
 games.sort((a,b)=>b.t-a.t||a.id.localeCompare(b.id));
 const summarize=n=>{
  const sample=games.slice(0,n),more=sample.filter(g=>g.value>line).length,less=sample.filter(g=>g.value<line).length,push=sample.length-more-less;
  return {sample:sample.length,more,less,push,moreRate:more/sample.length,lessRate:less/sample.length,pushRate:push/sample.length,mean:sample.reduce((s,g)=>s+g.value,0)/sample.length};
 };
 const all=summarize(games.length);
 return {status:'HISTORICAL_ONLY',...all,last5:summarize(5),last10:summarize(10),last15:summarize(15),modelValidated:false,betEligible:false,source:record.source};
}
module.exports={historyEvidence};
