/* Kenny's verified cross-sport moneyline parlay — no sportsbook-derived predictions. */
(()=>{'use strict';
const root=document.getElementById('ksl-best-ml-parlay');if(!root)return;
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const decimal=o=>o>0?1+o/100:1+100/(-o);
const american=d=>d>=2?'+'+Math.round((d-1)*100):'-'+Math.round(100/(d-1));
const age=t=>Date.now()-Date.parse(t);
const verified=r=>r&&r.market==='ML'&&r.data_status==='VERIFIED'&&r.simulation_status==='COMPLETE'&&r.price_verified===true&&Number.isInteger(r.simulations)&&r.simulations>=10000&&Number.isFinite(r.model_probability)&&r.model_probability>0&&r.model_probability<1&&Number.isFinite(r.odds)&&Math.abs(r.odds)>=100&&r.odds!==0&&r.model_source&& !['sportsbook','implied_odds'].includes(String(r.model_source).toLowerCase())&&r.selection&&r.event&&r.sport&&r.source&&['CONFIRMED','VERIFIED'].includes(r.lineup_status)&&age(r.odds_timestamp)>=0&&age(r.odds_timestamp)<=15*60000&&age(r.model_generated_at)>=0&&age(r.model_generated_at)<=60*60000&&Date.parse(r.start_time)>Date.now();
root.innerHTML='<div class="kml-head"><div><h2>🏆 Best Moneyline Parlay · All Sports</h2><p>Kenny’s verified projections only · +100 minimum · Monte Carlo</p></div><button id="kml-refresh" type="button">↻ Refresh</button></div><p id="kml-status" role="status">Checking Kenny’s model…</p><div id="kml-ticket"></div><p class="kml-note">One selection per game. Independent cross-game simulation; correlation calibration pending. Never substitute market-implied probabilities for model projections.</p>';
const status=document.getElementById('kml-status'),ticket=document.getElementById('kml-ticket'),button=document.getElementById('kml-refresh');
function best(rows){
 const unique=new Map();
 for(const r of rows.filter(verified)){const key=String(r.sport)+'|'+String(r.event_id||r.event);const old=unique.get(key)||[];old.push(r);unique.set(key,old)}
 const groups=[...unique.values()].map(a=>a.sort((x,y)=>y.model_probability*decimal(y.odds)-x.model_probability*decimal(x.odds)).slice(0,3));
 let winner=null;
 function visit(i,legs,d,p){if(legs.length>=2&&d>=2){const ev=p*d-1;if(ev>0&&(!winner||p>winner.p+1e-9||(Math.abs(p-winner.p)<1e-9&&ev>winner.ev)))winner={legs:[...legs],d,p,ev};}
 if(i>=groups.length||legs.length>=5)return;
 visit(i+1,legs,d,p);
 for(const r of groups[i])visit(i+1,[...legs,r],d*decimal(r.odds),p*r.model_probability);
 }
 // Limit search to highest-value 16 distinct events to keep mobile responsive.
 const limited=groups.sort((a,b)=>Math.max(...b.map(r=>r.model_probability))-Math.max(...a.map(r=>r.model_probability))).slice(0,16);
 groups.length=0;groups.push(...limited);visit(0,[],1,1);return winner;
}
function simulate(legs,n=50000){let wins=0;for(let i=0;i<n;i++){let hit=true;for(const r of legs){if(Math.random()>=r.model_probability){hit=false;break}}if(hit)wins++}return {wins,n,p:wins/n}}
async function refresh(){
 button.disabled=true;status.textContent='Loading verified Kenny’s model feed…';ticket.replaceChildren();
 try{const response=await fetch('./data/market_edges.json?ts='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error('Verified feed unavailable');const payload=await response.json(),rows=Array.isArray(payload)?payload:payload.edges;
 if(!Array.isArray(rows)||(!Array.isArray(payload)&&payload.status!=='VERIFIED'))throw Error(payload.reason||'Verified model feed unavailable');
 const eligible=rows.filter(verified),pick=best(eligible);
 if(!pick){status.textContent='UNAVAILABLE — no positive-EV +100 moneyline parlay has enough independently verified Kenny’s model inputs.';return}
 const mc=simulate(pick.legs),simEV=mc.p*pick.d-1;
 status.textContent='COMPLETE · '+mc.n.toLocaleString()+' Monte Carlo trials · '+pick.legs.length+' verified legs';
 ticket.innerHTML='<div class="kml-summary"><strong>'+american(pick.d)+'</strong><span>Simulated win '+(mc.p*100).toFixed(1)+'%</span><span>Model fair '+american(1/pick.p)+'</span><span>Simulated EV '+(simEV*100).toFixed(1)+'%</span></div>'+
 pick.legs.map(r=>'<div class="kml-leg"><b>'+esc(r.selection)+'</b><span>'+esc(r.sport)+' · '+esc(r.event)+'</span><span>'+esc(r.odds>0?'+'+r.odds:r.odds)+' · Kenny’s '+(r.model_probability*100).toFixed(1)+'% · '+r.simulations.toLocaleString()+' source simulations</span></div>').join('')+
 '<div class="kml-stake"><label>Stake $ <input id="kml-stake" type="number" min="1" value="25"></label><span id="kml-return"></span></div><small>Monte Carlo 95% sampling margin ±'+(196*Math.sqrt(mc.p*(1-mc.p)/mc.n)).toFixed(2)+' percentage points · independently sampled games · updated '+new Date().toLocaleTimeString()+'</small>';
 const stake=document.getElementById('kml-stake'),out=document.getElementById('kml-return');const calc=()=>{const x=Math.max(0,Number(stake.value)||0);out.textContent='Return $'+(x*pick.d).toFixed(2)+' · Profit $'+(x*(pick.d-1)).toFixed(2)};stake.addEventListener('input',calc);calc();
 }catch(e){status.textContent='UNAVAILABLE — '+String(e.message||'Verified feed could not be loaded');}
 finally{button.disabled=false}
}
button.addEventListener('click',refresh);refresh();
})();