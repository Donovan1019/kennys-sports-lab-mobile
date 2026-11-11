/* Four-sport homepage scanner. Verified upstream records only. */
(()=>{'use strict';
const sports=['NBA','NHL','NFL','NCAAB'],markets=['ML','SPREAD','TOTAL'];
const root=document.getElementById('ksl-market-edge');if(!root)return;
root.innerHTML='<div class="me-head"><div><h2>⚡ Market Mispricing Scanner</h2><p>NBA · NHL · NFL · NCAA Men • verified model vs sportsbook prices</p></div><button id="me-refresh" type="button">↻ Refresh</button></div><div class="me-filters"><select id="me-sport" aria-label="Sport"><option value="ALL">All sports</option>'+sports.map(s=>'<option>'+s+'</option>').join('')+'</select><select id="me-market" aria-label="Market"><option value="ALL">All markets</option><option value="ML">Moneyline</option><option value="SPREAD">Spread</option><option value="TOTAL">Total</option></select><label>Stake $ <input id="me-stake" type="number" min="1" max="10000" step="1" value="25" inputmode="decimal" aria-label="Stake in dollars" style="width:85px"></label><label>Minimum EV <select id="me-min"><option value="0">0%</option><option value="0.02" selected>2%</option><option value="0.05">5%</option></select></label></div><p id="me-status" role="status">Checking verified model feed…</p><div id="me-results"></div><p class="me-note">Only independently priced, simulated, timestamped upcoming markets appear. Missing or stale data is never represented as a pick.</p>';
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const prob=odds=>odds>0?100/(odds+100):-odds/(100-odds);
const payout=odds=>odds>0?odds/100:100/-odds;
const kelly=(p,odds)=>{const b=payout(odds);return Math.max(0,(p*b-(1-p))/b)};
const maxPrice=p=>p>=.5?-Math.ceil(100*p/(1-p)):Math.floor(100*(1-p)/p);
const tier=r=>r.ev>=.05&&r.simulations>=10000?'HIGH EV':r.ev>=.03?'MEDIUM EV':'LOW EV';
const american=p=>p>=.5?'-'+Math.round(100*p/(1-p)):'+'+Math.round(100*(1-p)/p);
const valid=r=>r&&sports.includes(r.sport)&&markets.includes(r.market)&&typeof r.event==='string'&&r.event.trim()&&typeof r.selection==='string'&&r.selection.trim()&&Number.isFinite(r.odds)&&r.odds!==0&&Math.abs(r.odds)>=100&&Number.isFinite(r.model_probability)&&r.model_probability>0&&r.model_probability<1&&Number.isInteger(r.simulations)&&r.simulations>=1000&&r.simulation_status==='COMPLETE'&&r.price_verified===true&&typeof r.source==='string'&&r.source.trim()&&Number.isFinite(Date.parse(r.odds_timestamp))&&Number.isFinite(Date.parse(r.start_time))&&Date.parse(r.start_time)>Date.now()&&Date.now()-Date.parse(r.odds_timestamp)>=0&&Date.now()-Date.parse(r.odds_timestamp)<=15*60*1000&&['CONFIRMED','VERIFIED'].includes(r.lineup_status)&&r.data_status==='VERIFIED'&&typeof r.model_source==='string'&&r.model_source.trim()&&r.model_source!=='sportsbook'&&r.model_source.toLowerCase()!=='implied_odds'&&Number.isFinite(Date.parse(r.model_generated_at))&&Date.now()-Date.parse(r.model_generated_at)>=0&&Date.now()-Date.parse(r.model_generated_at)<=60*60*1000&&(r.market==='ML'||(Number.isFinite(r.point)));
let rows=[];let feedStatus='';
function render(){const sport=$('me-sport').value,market=$('me-market').value,min=Number($('me-min').value);
const stake=Math.min(10000,Math.max(1,Number($('me-stake').value)||25));
const list=rows.filter(r=>valid(r)&&(sport==='ALL'||r.sport===sport)&&(market==='ALL'||r.market===market)&&r.ev>=min).sort((a,b)=>b.ev-a.ev).slice(0,10);
$('me-results').replaceChildren();if(!list.length){$('me-results').innerHTML='<p class="me-empty">'+esc(feedStatus||'No verified positive-EV candidates meet these filters. No picks generated.')+'</p>';return}
for(const r of list){
const item=document.createElement('article');item.className='me-card';
item.innerHTML='<div class="me-top"><strong>'+esc(r.sport)+' · '+esc(r.event)+'</strong><span>'+esc(r.market)+'</span></div>'+
'<h3>'+esc(r.selection)+(r.market==='ML'?'':' ('+esc(r.point>0?'+'+r.point:r.point)+')')+' <span class="me-tier">'+tier(r)+'</span></h3>'+
'<div class="me-metrics"><span>Odds <b>'+esc(r.odds>0?'+'+r.odds:r.odds)+'</b></span><span>Model <b>'+(100*r.model_probability).toFixed(1)+'%</b></span><span>Fair <b>'+american(r.model_probability)+'</b></span><span>EV <b class="me-positive">+'+(100*r.ev).toFixed(1)+'%</b></span></div>'+
'<div class="me-bet-details"><span>Break-even <b>'+(100*prob(r.odds)).toFixed(1)+'%</b></span><span>Probability edge <b>+'+(100*(r.model_probability-prob(r.odds))).toFixed(1)+' pp</b></span><span>Expected profit on $'+stake.toFixed(0)+' <b>+$'+(stake*r.ev).toFixed(2)+'</b></span><span>¼ Kelly, capped at 1% bankroll <b>'+(100*Math.min(.01,.25*kelly(r.model_probability,r.odds))).toFixed(2)+'%</b></span></div>'+
'<small>'+esc(r.source)+' · '+r.simulations.toLocaleString()+' simulations · updated '+new Date(r.odds_timestamp).toLocaleTimeString()+'</small>';
$('me-results').append(item);
}
}
async function refresh(){ $('me-status').textContent='Loading verified four-sport model feed…';$('me-refresh').disabled=true;
try{const res=await fetch('./data/market_edges.json?ts='+Date.now(),{cache:'no-store'});if(!res.ok)throw Error('Feed unavailable');const payload=await res.json();const entries=Array.isArray(payload)?payload:payload.edges;if(!Array.isArray(entries))throw Error('Invalid feed');
rows=entries.filter(valid).map(r=>({...r,ev:r.model_probability*payout(r.odds)-(1-r.model_probability)})).filter(r=>r.ev>0);feedStatus=payload.status==='UNAVAILABLE'?'UNAVAILABLE: '+String(payload.reason||'Verified upstream model or sportsbook data missing'):payload.status==='NO_QUALIFIED_EDGES'?'No qualifying positive-EV contracts in the verified feed.':'No picks match these filters.';
$('me-status').textContent=rows.length+' verified positive-EV candidates · '+sports.join(' / ')+(payload.status==='UNAVAILABLE'?' · FEED UNAVAILABLE: '+String(payload.reason||'no connected model candidates'):'');
}catch(e){rows=[];feedStatus='UNAVAILABLE: Could not load the verified market feed.';$('me-status').textContent=feedStatus;}
finally{$('me-refresh').disabled=false;render()}}
['me-sport','me-market','me-min','me-stake'].forEach(id=>$(id).addEventListener('change',render));$('me-refresh').addEventListener('click',refresh);refresh();
})();