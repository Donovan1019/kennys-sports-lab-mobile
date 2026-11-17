(()=>{'use strict';
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=v=>(100*v).toFixed(1)+'%';
const cents=v=>(100*v).toFixed(1)+'¢';
const sports={nba:'NBA',nfl:'NFL',nhl:'NHL',ncaab:'NCAAB'};
async function get(path){const res=await fetch(path+'?v='+Date.now(),{cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);return res.json()}
function fresh(date,maxMs){const t=Date.parse(date);return Number.isFinite(t)&&t<=Date.now()+300000&&Date.now()-t>=0&&Date.now()-t<=maxMs}
function render(feed){
 const rows=Array.isArray(feed.picks)?feed.picks:[];
 const sport=$('sport').value;
 const accepted=rows.filter(p=>p&&p.tier==='ADVANCED'&&p.verified===true&&p.contract_verified===true&&p.simulation_verified===true&&p.model_probability>0&&p.model_probability<1&&p.kalshi_ask>0&&p.kalshi_ask<1&&fresh(p.quote_at,3600000)&&(!p.start_time||Date.parse(p.start_time)>Date.now())&&(sport==='all'||p.sport===sport));
 const best=new Map();
 for(const p of accepted){const key=[p.sport,p.event_ticker,p.winner].join('|');const old=best.get(key);if(!old||(p.net_ev??-Infinity)>(old.net_ev??-Infinity))best.set(key,p)}
 const picks=[...best.values()].sort((a,b)=>b.model_probability-a.model_probability||((b.net_ev??-Infinity)-(a.net_ev??-Infinity))).slice(0,20);
 $('reviewStatus').textContent=picks.length?picks.length+' independently verified advanced outcomes · quotes checked within 60 minutes':'No verified advanced predictions available. Baseline estimates are excluded from the main Kalshi board.';
 $('ticker').textContent=picks.length?picks.slice(0,10).map(p=>sports[p.sport]+' · '+p.winner+' '+pct(p.model_probability)).join('     •     '):'Awaiting independently verified advanced sports projections';
 $('reviewCandidates').innerHTML=picks.map(p=>'<article class="market"><strong>'+esc(p.winner)+' wins</strong><p class="muted">'+esc(sports[p.sport]||p.sport)+' · '+esc(p.event||'')+'</p><div class="stats"><span>Model '+pct(p.model_probability)+'</span><span>Kalshi ask '+cents(p.kalshi_ask)+'</span><span>Price gap '+((p.model_probability-p.kalshi_ask)*100).toFixed(1)+' pts</span><span>Estimated net EV '+(Number.isFinite(p.net_ev)?cents(p.net_ev):'Not verified')+'</span></div><details><summary>Advanced model evidence</summary><p>'+esc(p.explanation||'Validated evidence available in source feed')+'</p></details><p><a href="https://kalshi.com/markets/'+encodeURIComponent(p.event_ticker)+'" target="_blank" rel="noopener noreferrer">View on Kalshi</a></p></article>').join('');
}
let loading=false;
async function load(){if(loading)return;loading=true;$('refresh').disabled=true;$('status').textContent='Checking advanced model evidence…';try{const feed=await get('./data/kalshi-advanced-picks.json');if(!fresh(feed.generated_at,3600000))throw Error('Advanced feed is stale or missing');render(feed);$('status').textContent='Advanced feed updated '+new Date(feed.generated_at).toLocaleString()+' · '+esc(feed.status||'unknown');}catch(e){$('reviewStatus').textContent='Advanced model feed unavailable: '+String(e.message||e);$('reviewCandidates').textContent='No predictions displayed without verified evidence.';$('ticker').textContent='Advanced predictions unavailable';$('status').textContent='Refresh required';}finally{loading=false;$('refresh').disabled=false}}
$('refresh').addEventListener('click',load);$('sport').addEventListener('change',load);load();setInterval(()=>{if(!document.hidden)load()},120000);
})();