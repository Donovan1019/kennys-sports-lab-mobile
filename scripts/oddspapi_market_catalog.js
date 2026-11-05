'use strict';
// Deterministic PrizePicks extraction; does not call the provider or consume quota.
function indexMarkets(markets){
 if(!Array.isArray(markets))throw Error('MARKET_CATALOG_INVALID');
 const byId=new Map();
 for(const m of markets){
  if(!Number.isInteger(m?.marketId)||typeof m.marketName!=='string'||!Number.isFinite(Number(m.handicap))||!Array.isArray(m.outcomes))continue;
  byId.set(String(m.marketId),{name:m.marketName,line:Number(m.handicap),outcomes:new Map(m.outcomes.filter(o=>o?.outcomeId!=null&&typeof o.outcomeName==='string').map(o=>[String(o.outcomeId),o.outcomeName]))});
 }
 return byId;
}
function parsePrizePicks(odds,marketCatalog,{now=Date.now(),maxAgeMs=30*60*1000}={}){
 if(!odds||typeof odds!=='object'||!marketCatalog?.get)throw Error('ODDS_SCHEMA_INVALID');
 const book=odds.bookmakerOdds?.prizepicks;
 if(!book||typeof book.markets!=='object'||book.markets===null)return {status:'NO_PRIZEPICKS_MARKETS',lines:[]};
 const lines=[],seen=new Set();
 for(const [marketId,market] of Object.entries(book.markets)){
  const meta=marketCatalog.get(marketId);if(!meta||!market?.outcomes)continue;
  for(const [outcomeId,outcome] of Object.entries(market.outcomes)){
   const side=meta.outcomes.get(outcomeId);
   if(!['Over','Under','More','Less'].includes(side)||!outcome?.players)continue;
   for(const [playerId,leg] of Object.entries(outcome.players)){
    if(leg?.active!==true||typeof leg.playerName!=='string'||!playerId||playerId==='0')continue;
    const changed=Date.parse(leg.changedAt||'');
    if(!Number.isFinite(changed)||changed>now+60000||now-changed>maxAgeMs)continue;
    const id=[odds.fixtureId,marketId,outcomeId,playerId].join(':');if(seen.has(id))continue;seen.add(id);
    lines.push({fixtureId:String(odds.fixtureId||''),playerId,playerName:leg.playerName,marketId,marketName:meta.name,line:meta.line,side,changedAt:new Date(changed).toISOString(),source:'oddspapi:prizepicks',betEligible:false,identityVerified:false});
   }
  }
 }
 return {status:lines.length?'RAW_LINES_ONLY':'NO_FRESH_ACTIVE_LINES',lines};
}
module.exports={indexMarkets,parsePrizePicks};
