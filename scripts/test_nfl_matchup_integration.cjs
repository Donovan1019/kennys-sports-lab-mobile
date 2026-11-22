const fs=require('node:fs');const assert=require('node:assert/strict');
const html=fs.readFileSync('gameday.html','utf8');
const js=fs.readFileSync('nfl_matchup_integrated_breakdown.js','utf8');
const must=(v,label)=>assert.ok(js.includes(v),label);
assert.ok(html.includes('nfl_matchup_integrated_breakdown.js'),'script mounted');
assert.ok(html.includes('id="game"'),'game selector retained');
for(const x of ['heatMap(g,rec,windowName)','hm-table','hm-soft','hm-middle','hm-tough','hm-possession','WHAT TO KNOW','QUARTERBACK','SKILL PLAYERS','TGT SHARE','EZ TGT/G','PPR AWAY','QB FANTASY PPR','shot-market','contextPanel(g,rec,windowName)','injuryPanel(g)','teamCards(g)','String(x.event_id)===String(g.id)','player_id','sample_size','defenseFresh'])must(x,x);
assert.ok(!js.includes("label.includes(selected.away)"),'no fragile selector-label match');
assert.ok(js.includes("Number(x.season)===season"),'current-season player logs only');
assert.ok(js.includes("'Pass Attempts'"),'actual feed key for attempts');
assert.ok(js.includes("player_id"),'stable opportunity player joins');
assert.ok(js.includes("awayPpr(logs"),'away splits calculated');
assert.ok(js.includes("values.length!==32"),'ranking requires minimum comparison-pool coverage');
assert.ok(js.includes('data-ready'),'original fallback retained');
must('HOW IT COULD PLAY OUT','scenarios');
console.log('NFL screenshot heat-map static contract checks passed');

assert.ok(js.includes('kickoffDate.getUTCMonth()<2?1:0'),'January and February games retain preceding NFL season');
assert.ok(js.includes('upstream ingestion must be repaired'),'empty player feeds surface actionable diagnostics');
assert.ok(js.includes('target shares and end-zone usage cannot be calculated'),'empty opportunity feeds never imply verified usage');

const nflNav=fs.readFileSync('nfl.html','utf8');
assert.ok(nflNav.includes('href="./gameday.html">GameDay</a>'),'NFL navigation exposes dedicated GameDay tab');
assert.ok(!nflNav.includes('href="./nfl-matchup-lab.html">Player Breakdown</a>'),'legacy placement removed');
assert.ok(fs.readFileSync('nfl-matchup-lab.html','utf8').includes('gameday.html'),'old page redirects to GameDay');

assert.ok(js.includes("['RB','WR','TE'].includes(String(x.position"),'opportunity rows include running backs');
assert.ok(js.includes('Date.parse(x.game_date)<kickoff'),'opportunity rows dated after kickoff are excluded');

assert.ok(js.includes("-2*sum(v,['Interceptions','Fumbles lost'])"),'standard PPR scoring subtracts turnovers');
assert.ok(js.includes("!Number.isFinite(Number(v))?'—'"),'non-numeric heatmap values display unavailable');

assert.ok(js.includes('const keys=[x.player_id,x.player_name]'),'opportunity rows index stable IDs and display names');
assert.ok(js.includes("byName.get(String(p.name||'').trim().toLowerCase())"),'opportunity lookup falls back to player name');
