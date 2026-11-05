'use strict';
const assert=require('node:assert/strict');
const {indexMarkets,parsePrizePicks}=require('../scripts/oddspapi_market_catalog');
const markets=indexMarkets([{marketId:123,marketName:'Over Under Player Shots',playerProp:true,handicap:2.5,outcomes:[{outcomeId:1,outcomeName:'Over'},{outcomeId:2,outcomeName:'Under'}]}]);
const t=Date.parse('2026-11-05T12:00:00Z');
const players={
 p42:{active:true,playerName:'Player One',changedAt:'2026-11-05T11:55:00Z'},
 p43:{active:false,playerName:'Player Two',changedAt:'2026-11-05T11:55:00Z'}
};
const odds={fixtureId:'id123',bookmakerOdds:{prizepicks:{bookmakerIsActive:true,suspended:false,markets:{123:{marketActive:true,outcomes:{1:{players}}}}}}};
const result=parsePrizePicks(odds,markets,{now:t});
assert.equal(result.status,'RAW_LINES_ONLY');
assert.equal(result.lines.length,1);
assert.equal(result.lines[0].playerId,'p42');
assert.equal(result.lines[0].line,2.5);
assert.equal(result.lines[0].betEligible,false);
assert.equal(parsePrizePicks(odds,markets,{now:t+3600000}).lines.length,0);
assert.equal(parsePrizePicks({fixtureId:'id123',bookmakerOdds:{}},markets,{now:t}).status,'NO_PRIZEPICKS_MARKETS');
assert.equal(parsePrizePicks({...odds,bookmakerOdds:{prizepicks:{...odds.bookmakerOdds.prizepicks,suspended:true}}},markets,{now:t}).lines.length,0);
assert.throws(()=>indexMarkets({}),/INVALID/);
console.log('OddsPapi market parser tests passed');
