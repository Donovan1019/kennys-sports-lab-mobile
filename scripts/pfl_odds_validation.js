#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
const allowedBooks=new Set(['onyx','draftkings','fanduel','betmgm']);
const allowedMarkets=new Set(['ml','total']);
const finite=x=>typeof x==='number'&&Number.isFinite(x);
function validate(rows,readiness,now=Date.now()){
 const ready=new Map((readiness.bouts||[]).map(b=>[String(b.boutId),b]));
 const accepted=[],rejected=[],seen=new Set();
 for(const raw of Array.isArray(rows)?rows:[]){
  const x=raw&&typeof raw==='object'?raw:{};
  const reasons=[];
  const bout=ready.get(String(x.fightId));
  if(!bout?.identityAndHistoryVerified)reasons.push('BOUT_NOT_VERIFIED');
  if(!allowedBooks.has(x.book))reasons.push('BOOK_NOT_VERIFIED');
  if(!allowedMarkets.has(x.market))reasons.push('MARKET_UNSUPPORTED');
  if(typeof x.selection!=='string'||!x.selection.trim())reasons.push('SELECTION_MISSING');
  if(!finite(x.odds)||x.odds===0||Math.abs(x.odds)<100)reasons.push('AMERICAN_ODDS_INVALID');
  if(x.market==='total'&&(!finite(x.line)||x.line<=0||!['over','under'].includes(x.side)||x.settlementVerified!==true))reasons.push('TOTAL_SETTLEMENT_UNVERIFIED');
  const ts=Date.parse(x.oddsTimestamp);
  if(!Number.isFinite(ts)||ts>now+300000||now-ts>7200000)reasons.push('ODDS_STALE');
  if(x.sourceVerified!==true)reasons.push('SOURCE_UNVERIFIED');
  if(x.fightStatus!=='scheduled')reasons.push('FIGHT_NOT_SCHEDULED');
  const key=[x.fightId,x.book,x.market,x.selection,x.line??'',x.side??''].join('|');
  if(seen.has(key))reasons.push('DUPLICATE_MARKET');seen.add(key);
  const item={...x,bookVerified:reasons.length===0,boutVerified:!!bout?.identityAndHistoryVerified,verified:reasons.length===0};
  if(reasons.length)rejected.push({fightId:x.fightId??null,book:x.book??null,market:x.market??null,reasons});
  else accepted.push(item);
 }
 return {schemaVersion:1,source:'pfl-odds-validation',generatedAt:new Date(now).toISOString(),accepted,rejected,bettingReady:false,reason:'Odds validation does not establish calibrated probabilities or completed Monte Carlo simulation'};
}
if(require.main===module){
 const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));
 const readiness=load('data/pfl/bout-readiness.json');
 const file='data/pfl/odds-input.json';
 const rows=fs.existsSync(file)?load(file):[];
 const out=validate(rows,readiness);
 fs.writeFileSync('data/pfl/odds-validation.json',JSON.stringify(out,null,2)+'\n');
 console.log('PFL odds validation:',JSON.stringify({accepted:out.accepted.length,rejected:out.rejected.length,bettingReady:false}));
}
module.exports={validate};
