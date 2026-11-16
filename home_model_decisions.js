(()=>{'use strict';
const main=document.querySelector('main'),anchor=document.getElementById('ksl-market-edge');if(!main||!anchor)return;const root=document.createElement('section');root.id='ksl-model-decisions';root.setAttribute('aria-label','Independent model market decisions');root.style.marginBottom='22px';main.insertBefore(root,anchor);
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=x=>Number.isFinite(x)?(x*100).toFixed(1)+'%':'—';
const status=x=>x==='BETTING_READY'?'BETTING READY':x==='NO_VALUE'?'NO VALUE':x==='NO_ROBUST_EDGE'?'UNCERTAIN EDGE':x==='PROVISIONAL'?'PROJECTION ONLY':'BLOCKED';
root.innerHTML='<h2>Independent Model · Market Decisions</h2><p>NBA · NHL · NCAA basketball | Model projections shown separately from price-qualified bets.</p><p id="kmd-status" role="status">Loading published decisions…</p><div id="kmd-rows"></div>';
fetch('./feed/model_market_decisions.json?ts='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Feed unavailable');return r.json()}).then(feed=>{
const stamp=Date.parse(feed.generated_at),age=Date.now()-stamp;
if(feed.status!=='ok'||!Number.isFinite(stamp)||age<0||age>24*3600000){root.querySelector('#kmd-status').textContent='Decision feed outdated or unavailable; no current recommendations.';return;}
const rows=(feed.decisions||[]).filter(r=>Number.isFinite(Date.parse(r.start_time))&&Date.parse(r.start_time)>Date.now()&&Number.isFinite(r.model_probability)&&r.model_probability>0&&r.model_probability<1);
root.querySelector('#kmd-status').textContent=rows.length?rows.length+' independent projections · feed '+new Date(stamp).toLocaleString():'No upcoming verified model projections in the published feed.';
const games=new Map();
for(const r of rows){
  const key=[r.sport,r.event_id||r.event,r.start_time].join('|');
  if(!games.has(key))games.set(key,{sport:r.sport,event:r.event,start:r.start_time,rows:[]});
  games.get(key).rows.push(r);
}
const priority=r=>r.bet_status==='BETTING_READY'?0:r.bet_status==='PROVISIONAL'?1:r.bet_status==='NO_VALUE'?2:3;
const gameList=[...games.values()].sort((a,b)=>Math.min(...a.rows.map(priority))-Math.min(...b.rows.map(priority))||Date.parse(a.start)-Date.parse(b.start));
root.querySelector('#kmd-status').textContent=gameList.length?gameList.length+' games · '+rows.length+' sportsbook comparisons · feed '+new Date(stamp).toLocaleString():'No upcoming verified model projections in the published feed.';
root.querySelector('#kmd-rows').innerHTML=gameList.slice(0,20).map(g=>{
  const teams=new Map();
  for(const r of g.rows){if(!teams.has(r.selection))teams.set(r.selection,[]);teams.get(r.selection).push(r);}
  const league=g.sport.replace('basketball_','').replace('icehockey_','').toUpperCase();
  const teamRows=[...teams.entries()].map(([team,quotes])=>{
    quotes.sort((a,b)=>String(a.bookmaker).localeCompare(String(b.bookmaker)));
    const base=quotes[0];
    const bookPrices=quotes.map(q=>'<span class="kmd-book">'+esc(q.bookmaker==='draftkings'?'DK':q.bookmaker==='fanduel'?'FD':q.bookmaker)+' <b>'+esc(q.offered_odds??'—')+'</b> <small>'+esc(status(q.bet_status))+'</small></span>').join('');
    return '<div class="kmd-team"><div class="kmd-team-info"><strong>'+esc(team)+'</strong><span>Model '+pct(base.model_probability)+' · Fair '+esc(base.fair_odds??'—')+'</span></div><div class="kmd-books">'+bookPrices+'</div></div>';
  }).join('');
  return '<article class="kmd-game"><div class="kmd-game-header"><strong>'+esc(league)+' · '+esc(g.event)+'</strong><span>'+esc(new Date(g.start).toLocaleString([], {month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}))+'</span></div>'+teamRows+'</article>';
}).join('');

}).catch(()=>{root.querySelector('#kmd-status').textContent='Decision feed unavailable; no picks can be verified.'});
})();