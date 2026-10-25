/* Game-level NFL projections integrated inside Player Projections. No synthetic bookmaker lines. */
(()=>{'use strict';if(window.KSL_ACTIVE_SPORT!=='NFL')return;
const root=document.getElementById('ksl-stat-root');if(!root)return;
const section=document.createElement('section');section.setAttribute('aria-label','NFL game and period projections');section.style.cssText='border:1px solid #45687d;border-radius:12px;padding:14px;margin:16px 0';
const title=document.createElement('h2');title.textContent='🏈 Game & Period Projections · Model Estimates';section.append(title);
const note=document.createElement('p');note.textContent='Inside the projection model: team-scoring simulations, not player-stat extrapolations. Full-game estimates are experimental; period markets require verified historical period scoring. No invented sportsbook prices.';section.append(note);
const market=document.createElement('select');market.setAttribute('aria-label','Game projection market');const period=document.createElement('select');period.setAttribute('aria-label','Game projection period');const matchup=document.createElement('select');matchup.setAttribute('aria-label','Game projection matchup');
for(const x of [market,period,matchup])x.style.cssText='padding:10px;margin:5px 6px 5px 0;max-width:100%;background:#10283a;color:white;border:1px solid #42677b;border-radius:8px';
for(const x of ['Moneyline','Spread','Game Total','Team Total']){const o=document.createElement('option');o.textContent=x;market.append(o)}
for(const x of ['Full game','1st half','2nd half','1st quarter','2nd quarter','3rd quarter','4th quarter']){const o=document.createElement('option');o.textContent=x;period.append(o)}
section.append(market,period,matchup);
const status=document.createElement('p');const output=document.createElement('div');section.append(status,output);
const attachToProjectionPanel=()=>{const playerBox=Array.from(document.querySelectorAll('section')).find(x=>x.querySelector('h2')?.textContent?.includes('Player Projections · Model Estimates'));if(!playerBox)return false;if(section.parentNode!==playerBox)playerBox.append(section);return true};if(!attachToProjectionPanel()){const observer=new MutationObserver(()=>{if(attachToProjectionPanel())observer.disconnect()});observer.observe(document.body,{childList:true,subtree:true})}
let games=[],quotes=[];const clean=x=>String(x||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const isRegular=x=>{const d=new Date(x.date);return Number.isFinite(d.getTime())&&d.getUTCMonth()!==7&&d.getTime()<Date.now()};
const history=t=>(t?.score_history||[]).filter(x=>isRegular(x)&&Number.isFinite(Number(x.scored))&&Number.isFinite(Number(x.allowed))).slice(0,12);
const mean=x=>x.reduce((a,b)=>a+b,0)/x.length;
const seedRand=key=>{let state=Array.from(key).reduce((h,c)=>(Math.imul(h,1664525)+c.charCodeAt(0)+1013904223)>>>0,2166136261)||1;return()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return (state+.5)/4294967296}};
const pct=(x,p)=>x[Math.max(0,Math.min(x.length-1,Math.floor(p*(x.length-1))))];
function simulation(g){const away=g.teams?.find(t=>clean(t.team)===clean(g.away)),home=g.teams?.find(t=>clean(t.team)===clean(g.home));const ah=history(away),hh=history(home);if(ah.length<8||hh.length<8)return null;
const af=mean(ah.map(x=>Number(x.scored))),aa=mean(ah.map(x=>Number(x.allowed))),hf=mean(hh.map(x=>Number(x.scored))),ha=mean(hh.map(x=>Number(x.allowed)));
const aMean=(af+ha)/2,hMean=(hf+aa)/2;
const rand=seedRand(g.event_id||g.event),draws=[];let aWins=0,hWins=0,ties=0;
for(let i=0;i<10000;i++){const ar=ah[Math.floor(rand()*ah.length)],hr=hh[Math.floor(rand()*hh.length)];const as=Math.max(0,aMean+.5*(Number(ar.scored)-af)+.5*(Number(hr.allowed)-ha));const hs=Math.max(0,hMean+.5*(Number(hr.scored)-hf)+.5*(Number(ar.allowed)-aa));draws.push({away:as,home:hs,total:as+hs,margin:hs-as});if(hs>as)hWins++;else if(as>hs)aWins++;else ties++}
const range=k=>{const x=draws.map(d=>d[k]).sort((a,b)=>a-b);return {mid:pct(x,.5),low:pct(x,.1),high:pct(x,.9)}};
return {aMean,hMean,away:range('away'),home:range('home'),total:range('total'),margin:range('margin'),aWins,hWins,ties,n:draws.length,ah:ah.length,hh:hh.length}}
const row=(label,value)=>{const d=document.createElement('div');d.style.cssText='display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid #29475b;flex-wrap:wrap';const l=document.createElement('span');l.textContent=label;const v=document.createElement('strong');v.textContent=value;d.append(l,v);return d};
const fmt=x=>Number(x).toFixed(1);
function draw(){output.replaceChildren();const g=games.find(x=>x.event_id===matchup.value);if(!g){status.textContent='No upcoming scheduled matchup with verified team inputs';return}
const card=document.createElement('article');card.style.cssText='border:1px solid #45687d;border-radius:12px;padding:14px;background:#10283a;margin-top:12px';
const h=document.createElement('h3');h.textContent=g.away+' @ '+g.home;card.append(h);
const label=period.value+' · '+market.value;card.append(row('Market',label));
if(period.value!=='Full game'){card.append(row('Projection','Awaiting verified period-by-period historical scoring data'),row('Simulation','Not run — full-game scores cannot validate quarter/half forecasts'),row('DK/FD','No verified current period lines in connected feed'));status.textContent='Period market selected · data integrity gate';output.append(card);return}
const sim=simulation(g);if(!sim){card.append(row('Projection','Insufficient verified regular-season team scoring history'),row('Simulation','Unavailable'));status.textContent='Historical data integrity gate';output.append(card);return}
status.textContent='10,000 game-level bootstrap simulations · '+sim.ah+' away-team and '+sim.hh+' home-team historical games · experimental';
if(market.value==='Moneyline'){card.append(row(g.home+' win simulation',fmt(100*sim.hWins/sim.n)+'%'),row(g.away+' win simulation',fmt(100*sim.aWins/sim.n)+'%'),row('Simulated ties',fmt(100*sim.ties/sim.n)+'%'))}
if(market.value==='Spread'){card.append(row('Home projected margin',fmt(sim.hMean-sim.aMean)),row('80% simulated home margin',fmt(sim.margin.low)+' to '+fmt(sim.margin.high)))}
if(market.value==='Game Total'){card.append(row('Projected total',fmt(sim.aMean+sim.hMean)),row('80% simulated total',fmt(sim.total.low)+' to '+fmt(sim.total.high)))}
if(market.value==='Team Total'){card.append(row(g.away+' projected points',fmt(sim.aMean)),row(g.away+' 80% range',fmt(sim.away.low)+' to '+fmt(sim.away.high)),row(g.home+' projected points',fmt(sim.hMean)),row(g.home+' 80% range',fmt(sim.home.low)+' to '+fmt(sim.home.high)))}
card.append(row('DraftKings / FanDuel','No verified current matching game-market quote'),row('Validation','EXPERIMENTAL · not calibrated · no injury/starting-lineup verification'));output.append(card)}
for(const x of [market,period,matchup])x.addEventListener('change',draw);
fetch('./feed/independent_game_inputs.json?game_projection='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('inputs unavailable');return r.json()}).then(d=>{games=(d.games||[]).filter(g=>Date.parse(g.commence_time)>Date.now()&&Array.isArray(g.teams)&&g.teams.length===2).sort((a,b)=>Date.parse(a.commence_time)-Date.parse(b.commence_time));for(const g of games){const o=document.createElement('option');o.value=g.event_id;o.textContent=g.event;matchup.append(o)}draw()}).catch(()=>{status.textContent='Independent team scoring feed unavailable; projections disabled'});
})();
