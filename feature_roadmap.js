/* Screenshot-inspired feature coverage audit. Statuses are explicit and never imply unbuilt analytics. */
(()=>{'use strict';
const features=[
['Player Board','Verified 2025/2026 game logs, threshold hit rates','available'],
['Sportsbook Odds','FanDuel/DraftKings core lines and NFL player props','available'],
['NFL Prop Monte Carlo','Historical bootstrap; not calibrated predictive simulation','experimental'],
['Top Trends','Ranked verified 5/5, 8/10, 10/10 streaks by market','partial'],
['Team Board','Every matchup, season trends, game projections','missing'],
['Match Simulations · Teams','Win %, scores, totals, spreads, uncertainty','missing'],
['Match Simulations · Players','Distribution and alternate-line probabilities','missing'],
['Head-to-Head Research','Historical meetings, custom lines and chart','missing'],
['Team Cheat Sheet','Offense/defense splits and player matchups','missing'],
['Defensive Analysis','Opponent position allowances and matchup grades','missing'],
['Stadium & Weather','Verified weather, wind and venue effects','missing'],
['Favorite Targets','Data-backed player and team watchlists','missing'],
['Player Stats Research','Game logs, recent charts, opponent splits','partial'],
['After the Games','Results, prediction error, CLV and calibration','missing'],
['Top Simulations','Cross-sport ranked validated opportunities','missing'],
['Soccer & NHL Trends','League-specific tables and projections','missing'],
['Kenny’s SGP','Per-team QB/WR/RB/team-total audit for each NFL game','partial'],
['Full Multi-Sport Coverage','Verified feeds, models and screens for every sport','missing']
];
const s=document.createElement('section');s.id='ksl-features';
s.innerHTML='<h2>Complete Feature Tracker</h2><p class="ksl-features-note">Based on your reference screenshots. Available means a working component exists; experimental and partial are not finished. Missing modules are not represented as working analytics.</p><div class="ksl-features-grid"></div>';
const css=document.createElement('style');css.textContent='#ksl-features{background:#101a17;border:1px solid #2a5744;border-radius:14px;margin:18px 0;padding:16px}#ksl-features h2{color:#70ef91}#ksl-features .ksl-features-note{font-size:13px;color:#b4c6bb;line-height:1.5}#ksl-features .ksl-features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}#ksl-features article{border:1px solid #355643;border-radius:10px;padding:12px}#ksl-features article strong{display:block}#ksl-features article p{color:#b4c6bb;font-size:12px;line-height:1.4}#ksl-features article small{font-weight:800;text-transform:uppercase;color:#c3e2d0}';document.head.append(css);
for(const [name,description,status] of features){const article=document.createElement('article');const title=document.createElement('strong');title.textContent=name;const detail=document.createElement('p');detail.textContent=description;const state=document.createElement('small');state.textContent=status;article.append(title,detail,state);s.querySelector('.ksl-features-grid').append(article)}
(document.querySelector('main')||document.body).append(s);
})();