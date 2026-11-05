/* Static regression checks for the NBA prop research UI; run with node. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const html=fs.readFileSync('nba-props.html','utf8');
const js=fs.readFileSync('nba_prop_research.js','utf8');
const nba=fs.readFileSync('nba.html','utf8');
assert.match(html,/nba_prop_research\.js/);
assert.match(nba,/nba-props\.html/);
for(const market of ['Points','Rebounds','Assists','Threes','Pts+Reb','Pts+Ast','Reb+Ast','PRA','Steals','Blocks','Turnovers','Stocks'])assert.match(js,new RegExp(market));
for(const tab of ['Graph','Shooting','Similar','Types'])assert.ok(js.includes("'"+tab+"'"));
assert.match(js,/feed\/nba_player_stats\.json/);
assert.match(js,/Number\(x\.g\.values&&x\.g\.values\.Minutes\)>0/);
assert.match(js,/No synthetic player data/);assert.match(js,/nba_player_walkforward_research.json/);assert.match(js,/LEAGUE-WIDE MODEL MAE/);assert.match(js,/research only/);
assert.match(js,/requires verified tracking/);
assert.doesNotMatch(js,/Math\.random\(/);
console.log('NBA prop research static checks passed');
