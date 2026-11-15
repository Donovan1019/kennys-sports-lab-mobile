(()=>{'use strict';
const root=document.getElementById('ksl-model-decisions');if(!root)return;
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=x=>Number.isFinite(x)?(x*100).toFixed(1)+'%':'—';
const status=x=>x==='BETTING_READY'?'BETTING READY':x==='NO_VALUE'?'NO VALUE':x==='NO_ROBUST_EDGE'?'UNCERTAIN EDGE':x==='PROVISIONAL'?'PROJECTION ONLY':'BLOCKED';
root.innerHTML='<h2>Independent Model · Market Decisions</h2><p>NBA · NHL · NCAA basketball | Model projections shown separately from price-qualified bets.</p><p id="kmd-status" role="status">Loading published decisions…</p><div id="kmd-rows"></div>';
fetch('./feed/model_market_decisions.json?ts='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Feed unavailable');return r.json()}).then(feed=>{
const stamp=Date.parse(feed.generated_at),age=Date.now()-stamp;
if(feed.status!=='ok'||!Number.isFinite(stamp)||age<0||age>24*3600000){root.querySelector('#kmd-status').textContent='Decision feed outdated or unavailable; no current recommendations.';return;}
const rows=(feed.decisions||[]).filter(r=>Number.isFinite(Date.parse(r.start_time))&&Date.parse(r.start_time)>Date.now()&&Number.isFinite(r.model_probability)&&r.model_probability>0&&r.model_probability<1);
root.querySelector('#kmd-status').textContent=rows.length?rows.length+' independent projections · feed '+new Date(stamp).toLocaleString():'No upcoming verified model projections in the published feed.';
rows.sort((a,b)=>(a.bet_status==='BETTING_READY'?-1:0)-(b.bet_status==='BETTING_READY'?-1:0));
root.querySelector('#kmd-rows').innerHTML=rows.slice(0,20).map(r=>'<article class="kmd-card"><div><strong>'+esc(r.sport.replace('basketball_','').replace('icehockey_','').toUpperCase())+' · '+esc(r.selection)+'</strong><div class="kmd-muted">'+esc(r.event)+' · '+esc(r.bookmaker)+'</div></div><div><span class="kmd-state">'+esc(status(r.bet_status))+'</span><div>Model '+pct(r.model_probability)+' · Fair '+esc(r.fair_odds??'—')+'</div><div class="kmd-muted">'+(r.bet_status==='BETTING_READY'&&Number.isFinite(r.expected_value)?'EV '+pct(r.expected_value):esc(r.reason||'Price not certified'))+'</div></div></article>').join('');
}).catch(()=>{root.querySelector('#kmd-status').textContent='Decision feed unavailable; no picks can be verified.'});
})();