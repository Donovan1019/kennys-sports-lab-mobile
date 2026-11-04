'use strict';
const assert=require('node:assert/strict');
const {boxscore,records}=require('../scripts/prizepicks_nba_espn_fallback');
const now=Date.parse('2026-11-04T20:00:00Z');
function sample(id){return {header:{competitions:[{date:'2026-10-15T00:00:00Z',status:{type:{state:'post'}}}]},boxscore:{players:[{statistics:[{labels:['PTS','REB','AST','3PT','FG','FT','TO'],athletes:[{athlete:{id:'123',displayName:'Jane Example'},stats:['22','8','5','3-7','8-15','3-4','2']}]}]}]}}}
const parsed=boxscore(sample('1'),'401234567',now);
assert.equal(parsed.length,1);assert.equal(parsed[0].stats.PTS,22);assert.equal(parsed[0].stats['3PTM'],3);
assert.equal(parsed[0].stats.FGM,8);assert.equal(parsed[0].stats.FGA,15);
const games=Array.from({length:15},(_,i)=>({...parsed[0],game:String(401234567+i),date:new Date(now-(i+1)*86400000).toISOString()}));
const history=records(games,{lines:[{league:'NBA',player:'Jane Example',player_id:'9999'}]});
assert.ok(history.some(x=>x.market==='Points'&&x.games.length===15));
assert.ok(history.every(x=>x.playerId==='123'&&x.source==='espn-public-boxscore'));
assert.equal(records(games.concat(games.map(g=>({...g,id:'456'}))),{lines:[{league:'NBA',player:'Jane Example'}]}).length,0);
assert.equal(boxscore({...sample(),header:{competitions:[{date:'2026-10-15T00:00:00Z',status:{type:{state:'pre'}}}]}},'1',now).length,0);
console.log('ESPN fallback boxscore, market and identity safety tests passed');
