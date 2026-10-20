(()=>{'use strict';
const host=document.getElementById('ksl-nba');if(!host)return;
const panel=document.createElement('section');panel.id='ksl-nba-predictive';panel.style.cssText='padding:14px;margin:12px 0;background:#122d38;border:1px solid #65a4aa;border-radius:12px;color:#f0f8fa';
panel.innerHTML='<h3>NBA Predictive Research Engine · 10,000 Simulations</h3><p id="nba-predict-status">Loading historical team and player results…</p><div id="nba-predict-results"></div><p style="font-size:12px;color:#b7d0d8">Experimental projections, not calibrated betting edges. Injury, confirmed lineup, live odds, position matchups, and sportsbook player markets are not integrated. Do not treat these estimates as verified picks.</p>';
host.prepend(panel);
const el=id=>document.getElementById(id),write=(parent,tag,text)=>{const n=document.createElement(tag);n.textContent=text;parent.append(n);return n};
const rng=(seed)=>()=>{seed=(Math.imul(seed,1664525)+1013904223)|0;return(seed>>>0)/4294967296};
const average=a=>a.reduce((s,v)=>s+v,0)/a.length;
const sd=a=>Math.sqrt(average(a.map(v=>(v-average(a))**2)));
const american=p=>p>=.5?'-'+Math.round(100*p/(1-p)):'+'+Math.round(100*(1-p)/p);
const fmt=x=>Number(x).toFixed(1);
const valid=g=>Number.isFinite(g.home_score)&&Number.isFinite(g.away_score);
const date=x=>String(x).slice(0,10);
async function load(){
try{
const [games,players,odds]=await Promise.all(['nba_completed_games.json','nba_player_stats.json','basketball_nba.json'].map(async n=>{const r=await fetch('./feed/'+n+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(n+' HTTP '+r.status);return r.json()}));
if(!Array.isArray(games.games)||!Array.isArray(players.players)||!Array.isArray(odds.odds))throw Error('Invalid feed schema');
const historical=games.games.filter(valid).filter(g=>date(g.date)>='2025-10-01'&&date(g.date)<='2026-06-30');
const leaguePoints=historical.flatMap(g=>[g.home_score,g.away_score]);if(historical.length<100)throw Error('Insufficient completed NBA game history');
const leagueAvg=average(leaguePoints);
const teamHistory=new Map();for(const g of historical){for(const [team,scored,allowed] of [[g.home,g.home_score,g.away_score],[g.away,g.away_score,g.home_score]]){if(!teamHistory.has(team))teamHistory.set(team,[]);teamHistory.get(team).push({date:date(g.date),scored,allowed})}}
for(const rows of teamHistory.values())rows.sort((a,b)=>b.date.localeCompare(a.date));
const upcoming=[...new Map(odds.odds.filter(x=>x.event_id&&x.commence_time&&Date.parse(x.commence_time)>Date.now()-7200000).map(x=>[x.event_id,x])).values()].sort((a,b)=>Date.parse(a.commence_time)-Date.parse(b.commence_time)).slice(0,18);
const out=el('nba-predict-results');out.replaceChildren();
let n=0;
for(const game of upcoming){
const parts=game.event.split(' @ ');if(parts.length!==2)continue;
const [away,home]=parts;const ah=teamHistory.get(away)||[],hh=teamHistory.get(home)||[];if(ah.length<15||hh.length<15){write(out,'p',game.event+' · PASS: fewer than 15 historical team games');continue}
const shrink=10;const rate=(rows,key)=>(rows.slice(0,50).reduce((s,r)=>s+r[key],0)+shrink*leagueAvg)/(Math.min(50,rows.length)+shrink);
const awayMean=(rate(ah,'scored')+rate(hh,'allowed'))/2,homeMean=(rate(hh,'scored')+rate(ah,'allowed'))/2+2;
const variance=Math.max(9,sd(leaguePoints)*.85);
const rand=rng([...game.event].reduce((s,c)=>Math.imul(s,31)+c.charCodeAt(0),12345));
let wins=0,totals=[],margins=[];
for(let i=0;i<10000;i++){const gauss=()=>Math.sqrt(-2*Math.log(Math.max(rand(),1e-9)))*Math.cos(2*Math.PI*rand());const a=awayMean+gauss()*variance,h=homeMean+gauss()*variance;wins+=h>a;totals.push(a+h);margins.push(h-a)}
const homeProb=wins/10000,section=write(out,'details','');section.open=n<2;write(section,'summary',game.event+' · '+new Date(game.commence_time).toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})+' ET');
write(section,'p','Model: '+away+' '+fmt(awayMean)+' – '+home+' '+fmt(homeMean)+' · Total '+fmt(awayMean+homeMean)+' · '+home+' win '+fmt(homeProb*100)+'% (fair '+american(Math.min(.999,Math.max(.001,homeProb)))+')');
write(section,'p','Simulation: 10,000 synthetic game outcomes · mean total '+fmt(average(totals))+' · mean home margin '+fmt(average(margins))+' · model uncertainty not independently calibrated.');
const roster=players.players.filter(p=>p.team===({ 'New York Knicks':'NY','Golden State Warriors':'GS','San Antonio Spurs':'SA','New Orleans Pelicans':'NO','Utah Jazz':'UTAH'}[home]||home.split(' ').map(x=>x[0]).join(''))||p.team===({'New York Knicks':'NY','Golden State Warriors':'GS','San Antonio Spurs':'SA','New Orleans Pelicans':'NO','Utah Jazz':'UTAH'}[away]||away.split(' ').map(x=>x[0]).join('')));
let candidates=0;for(const p of roster){const rows=p.games.filter(g=>g.season==='2025-26'&&g.season_type==='regular').sort((a,b)=>b.date.localeCompare(a.date)).slice(0,30);if(rows.length<10)continue;const values=rows.map(g=>g.values.Points).filter(Number.isFinite);if(values.length<10)continue;const mean=average(values),hit=values.filter(v=>v>=15).length/values.length;write(section,'p',p.name+' ('+p.team+') · '+values.length+' games · PTS avg '+fmt(mean)+' · 15+ PTS '+fmt(hit*100)+'% historical (not priced)');if(++candidates>=8)break}
if(!candidates)write(section,'p','Player projections unavailable: roster/team mapping or qualifying game logs missing.');
n++;
}
el('nba-predict-status').textContent='Loaded '+historical.length+' historical completed games · '+players.players.length+' player histories · '+n+' upcoming matchups. Baseline model, no verified injury or live odds adjustments.';
if(!n)write(out,'p','No future NBA games found in the saved odds snapshot. Re-run the odds refresh to populate matchups.');
}catch(e){el('nba-predict-status').textContent='PREDICTIVE ENGINE UNAVAILABLE: '+e.message}
}
load();
})();