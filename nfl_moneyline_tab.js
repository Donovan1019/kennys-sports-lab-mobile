/* Dedicated NFL Moneyline tab reuses the existing historical-scoring simulation engine. */
(()=>{'use strict';
const host=document.getElementById('nfl-moneyline-content');
const status=document.getElementById('nfl-moneyline-status');
if(!host||!status)return;
const activate=()=>{
 const engine=document.getElementById('nfl-game-projections');
 if(!engine)return false;
 /* Keep the original projection engine in its existing player-projections location. */
 const market=engine.querySelector('select[aria-label="Game projection market"]');
 const period=engine.querySelector('select[aria-label="Game projection period"]');
 if(market&&market.value!=='Moneyline'){market.value='Moneyline';market.dispatchEvent(new Event('change',{bubbles:true}));}
 if(period&&period.value!=='Full game'){period.value='Full game';period.dispatchEvent(new Event('change',{bubbles:true}));}
 status.textContent='Moneyline model loaded · historical team scoring, simulated win probability and verified market comparisons when available. Research only.';
 return true;
};
const board=document.createElement('div');board.id='nfl-moneyline-board';host.prepend(board);
const clean=x=>String(x||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const odds=p=>p>0&&p<1?(p>=.5?'-'+Math.round(100*p/(1-p)):'+'+Math.round(100*(1-p)/p)):'N/A';
const dec=p=>p>0?1+p/100:1+100/Math.abs(p);
const row=(g,team,p,sim,quotes,stale)=>{const q=quotes.filter(x=>x.market==='h2h'&&clean(x.selection)===clean(team)&&clean(x.event)===clean(g.event)&&Math.abs(Date.parse(x.commence_time)-Date.parse(g.commence_time))<=600000&&['draftkings','fanduel'].includes(String(x.bookmaker).toLowerCase())&&Number.isFinite(x.price)&&Math.abs(x.price)>=100&&Number.isFinite(Date.parse(x.updated_at))&&Date.now()-Date.parse(x.updated_at)<=21600000&&Date.parse(x.updated_at)<=Date.now()+60000&&Date.parse(g.commence_time)>Date.now()).sort((a,b)=>dec(b.price)-dec(a.price))[0];const ev=q?(p*(dec(q.price)-1)-(1-p-sim.ties/sim.n))*100:null;return {g,team,p,sim,q,ev,stale}};
const drawBoard=()=>{const api=window.KSL_NFL_ML_ENGINE;if(!api)return;const games=api.getGames(),ts=Date.parse(api.getInputTimestamp()),stale=!Number.isFinite(ts)||ts>Date.now()||Date.now()-ts>7*86400000;const records=[];for(const g of games){const sim=api.simulation(g);if(!sim)continue;records.push(row(g,g.away,sim.aWins/sim.n,sim,api.matchQuotes(),stale),row(g,g.home,sim.hWins/sim.n,sim,api.matchQuotes(),stale))}board.replaceChildren();const heading=document.createElement('h3');heading.textContent='Full-slate moneyline leaderboard · both sides';board.append(heading);const note=document.createElement('p');note.textContent=stale?'Historical inputs stale or unverified · all outcomes research only':'Historical inputs timestamp checked · model remains uncalibrated and research only';board.append(note);const refresh=document.createElement('button');refresh.textContent='Refresh moneyline odds';refresh.onclick=()=>api.refreshOdds().then(drawBoard);board.append(refresh);const sort=document.createElement('select');sort.setAttribute('aria-label','Moneyline ranking');for(const [v,t] of [['ev','Research EV (high to low)'],['p','Win probability (high to low)'],['time','Kickoff (ET)']])sort.add(new Option(t,v));board.append(sort);const wrap=document.createElement('div');wrap.style.cssText='overflow-x:auto;margin-top:12px';const table=document.createElement('table');table.style.cssText='width:100%;min-width:650px;border-collapse:collapse';wrap.append(table);board.append(wrap);const render=()=>{table.replaceChildren();const head=document.createElement('tr');for(const t of ['Kickoff ET','Selection','Model win','Fair odds','Best verified DK/FD','Research EV','Status']){const th=document.createElement('th');th.textContent=t;head.append(th)}table.append(head);const sorted=records.slice().sort((a,b)=>sort.value==='time'?Date.parse(a.g.commence_time)-Date.parse(b.g.commence_time):sort.value==='p'?b.p-a.p:(b.ev??-Infinity)-(a.ev??-Infinity));for(const r of sorted){const tr=document.createElement('tr');const cells=[new Date(r.g.commence_time).toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}),r.team+' ML', (r.p*100).toFixed(1)+'%',odds(r.p),r.q?r.q.bookmaker.toUpperCase()+' '+(r.q.price>0?'+':'')+r.q.price:'UNAVAILABLE',r.ev==null?'UNAVAILABLE':r.ev.toFixed(1)+'%',r.stale?'STALE · PASS':'RESEARCH ONLY'];for(const val of cells){const td=document.createElement('td');td.textContent=val;td.style.cssText='padding:9px;border-bottom:1px solid #34506a;white-space:nowrap';tr.append(td)}table.append(tr)}if(!records.length){const p=document.createElement('p');p.textContent='No upcoming games with sufficient verified scoring history. Simulations unavailable.';board.append(p)}};sort.onchange=render;render()};
window.addEventListener('ksl-nfl-moneyline-ready',drawBoard);setTimeout(drawBoard,1000);
activate();
const observer=new MutationObserver(()=>{if(activate())observer.disconnect()});
observer.observe(document.body,{childList:true,subtree:true});
setTimeout(()=>{observer.disconnect();if(!document.getElementById('nfl-game-projections'))status.textContent='Moneyline engine unavailable. Check NFL game-projection data and refresh.'},20000);
})();