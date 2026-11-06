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
assert.match(js,/No synthetic player data/);assert.match(js,/nba_player_walkforward_research.json/);assert.match(js,/LEAGUE-WIDE MODEL MAE/);assert.match(js,/research only/);assert.match(js,/active==='Similar'/);assert.match(js,/Math.abs\(x.avg-r.avg\)/);assert.match(js,/descriptive comparison only/);assert.match(js,/active==='Types'/);assert.match(js,/Recorded stat-type breakdown/);assert.match(js,/not shot locations, play-type tracking/);assert.match(js,/active==='Shooting'/);assert.match(js,/eligible\.filter\(x=>latestSeason&&x\.g\.season===latestSeason\)/);assert.match(js,/history\.filter\(g=>latestSeason&&g\.season===latestSeason\)/);assert.match(js,/INCOMPLETE WINDOW/);assert.match(js,/SMALL SAMPLE/);assert.match(js,/Latest recorded:/);assert.match(js,/CROSSES SEASONS/);assert.match(js,/Show more players/);assert.match(js,/refresh-research/);assert.match(js,/window\.location\.reload\(\)/);assert.match(html,/Refresh saved research feeds/);assert.match(js,/visibleLimit\+=40/);assert.match(js,/rows\.slice\(0,visibleLimit\)/);assert.match(js,/new Set\(r\.games\.map\(x=>x\.g\.season\)/);assert.match(js,/shot coordinates, shooting percentages, or zones/);assert.match(js,/value\(g,'Threes'\)/);
assert.match(js,/requires verified tracking/);
assert.doesNotMatch(js,/Math\.random\(/);
console.log('NBA prop research static checks passed');

assert.match(js,/quote-placeholder/);assert.match(js,/player-research/);assert.match(js,/SEASON AVG/);assert.match(js,/reference-subtabs/);assert.match(html,/Screenshot-reference layout/);
