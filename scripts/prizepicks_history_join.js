/* Join provider source lines to separately verified historical game logs. No inferred identities. */
'use strict';
const {historyEvidence}=require('./prizepicks_history_evidence');
const NFL_ALIASES=Object.freeze({'pass yards':'Passing yards','passing yards':'Passing yards','pass tds':'Passing touchdowns','passing touchdowns':'Passing touchdowns','rush yards':'Rushing yards','rushing yards':'Rushing yards','rec yards':'Receiving yards','receiving yards':'Receiving yards','receptions':'Receptions','rush tds':'Rushing touchdowns','rushing touchdowns':'Rushing touchdowns','rec tds':'Receiving touchdowns','receiving touchdowns':'Receiving touchdowns'});
function canonicalMarket(league,market){return league==='NFL'?(NFL_ALIASES[String(market||'').trim().toLowerCase()]||market):market;}
function joinHistory(feed,records,now=Date.now()){
 if(!feed||feed.status!=='RAW_LINES_ONLY'||!Array.isArray(feed.lines)||!Array.isArray(records))return {status:'UNAVAILABLE',reason:'source or history schema missing',rows:[]};
 const seen=new Map();for(const r of records){if(!r||!r.providerPlayerId||!r.league||!r.market||!r.period)continue;const key=[r.league,r.providerPlayerId,canonicalMarket(r.league,r.market),r.period].join('|');if(seen.has(key))seen.set(key,null);else seen.set(key,r)}
 const rows=feed.lines.map(line=>{const key=[line.league,line.player_id,canonicalMarket(line.league,line.market),line.period].join('|');const record=line.player_id?seen.get(key):null;const evidence=record?historyEvidence(record,line.line,now):{status:'UNAVAILABLE',reason:'no unique verified player ID and matching market history'};return {id:line.id,league:line.league,player:line.player,market:line.market,line:line.line,history:evidence,modelValidated:false,betEligible:false}});
 return {status:'HISTORICAL_RESEARCH_ONLY',generated_at:new Date(now).toISOString(),rows};
}
module.exports={joinHistory,canonicalMarket};
