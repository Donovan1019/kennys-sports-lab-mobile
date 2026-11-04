'use strict';const assert=require('node:assert/strict');const {build}=require('../scripts/prizepicks_identity_candidates');const feed={lines:[{league:'NBA',player_id:'pp1',player:'Jane Doe'},{league:'NHL',player_id:'ppNHL',player:'Alex Example'}]};const history={records:[{league:'NBA',playerId:'espn2'}],diagnostics:{identityCandidates:[{prizepicksPlayerId:'pp1',espnCandidateIds:['espn2']} ]}};const result=build(feed,history);assert.equal(result.status,'UNVERIFIED_CANDIDATES_ONLY');assert.equal(result.rows[0].verified,false);assert.equal(result.rows[0].status,'REQUIRES_INDEPENDENT_ID_EVIDENCE');assert.equal(result.verifiedMappings,0);assert.equal(result.rows.length,2);assert.equal(result.rows.find(x=>x.league==='NHL').status,'NO_HISTORY_MATCH');assert.equal(result.rows.find(x=>x.league==='NHL').verified,false);const nhl={records:[{league:'NHL',playerId:'123'}],diagnostics:{identityCandidates:[{prizepicksPlayerId:'ppNHL',nhlCandidateIds:['123']} ]}};
const joined=build(feed,history,nhl);
assert.deepEqual(joined.rows.find(x=>x.league==='NHL').historyCandidateIds,['123']);
assert.equal(joined.rows.find(x=>x.league==='NHL').status,'REQUIRES_INDEPENDENT_ID_EVIDENCE');
assert.equal(joined.verifiedMappings,0);
const collision=build({lines:[...feed.lines,{league:'NHL',player_id:'ppNHL',player:'Different Person'}]},history,nhl);
assert.equal(collision.rows.find(x=>x.league==='NHL').status,'CONFLICTING_PROVIDER_NAMES');
assert.deepEqual(collision.rows.find(x=>x.league==='NHL').historyCandidateIds,[]);
console.log('identity candidate report safety passed');