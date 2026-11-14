/* PFL board recovery: schedule is independent of enrichment and betting feed. */
(()=>{'use strict';
const byId=id=>document.getElementById(id);
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const day=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const eligible=(e,b)=>e.status==='scheduled'&&b.status==='scheduled'&&/^\d{4}-\d{2}-\d{2}$/.test(e.date||'')&&e.date>=day()&&!b.winnerFighterSlug&&!b.method&&!b.resultRound;
let bouts=[],enrichment=null,hydrated=false;
function model(b){
 const p=(enrichment?.projections?.bouts||[]).find(x=>String(x.boutId)===String(b.id)&&x.available===true);
 let winner='<div class="ksl-pfl-prediction-pending">MODEL WINNER: PENDING <small>Verified fighter history insufficient</small></div>';
 if(p&&Array.isArray(p.fighters)&&p.fighters.length===2&&Number.isFinite(p.probabilityA)&&Number.isFinite(p.probabilityB)&&Math.abs(p.probabilityA+p.probabilityB-1)<.02){
 const first=p.probabilityA>=p.probabilityB;const name=(b.fighters||[])[first?0:1]?.name||p.fighters[first?0:1];const probability=Math.max(p.probabilityA,p.probabilityB);
 winner='<div class="ksl-pfl-prediction-win"><span>MODEL PREDICTED WINNER · EXPLORATORY</span><strong>'+escape(name)+'</strong><small>'+(probability*100).toFixed(1)+'% · uncalibrated</small></div>';
 }
 return '<div class="ksl-pfl-predictions">'+winner+'<div class="ksl-pfl-prediction-pending">TOTAL ROUNDS: MODEL PENDING <small>Validated finish-time distribution unavailable</small></div></div>';
}
function render(){
 const q=(byId('fight-search')?.value||'').trim().toLowerCase(),only=byId('only-ready')?.value||'all',sort=byId('sort')?.value||'date';
 let visible=bouts.filter(b=>[b.eventName,...(b.fighters||[]).map(x=>x.name)].join(' ').toLowerCase().includes(q));
 if(only==='ready')visible=[]; // No calibrated model + verified sportsbook markets currently available.
 if(sort==='date')visible.sort((a,b)=>a.date.localeCompare(b.date));
 const board=byId('fight-board');if(!board)return;
 if(!hydrated)return; // Keep the HTML-rendered schedule until a successful fetch. 
 board.innerHTML=visible.length?visible.map(b=>'<article class="ksl-pfl-fight"><div><small class="ksl-pfl-eyebrow">'+escape(b.eventName)+'</small><h3>'+escape((b.fighters||[]).map(x=>x.name||x.slug).join(' vs '))+'</h3><small class="ksl-pfl-muted">'+escape(b.date)+' · '+escape(b.scheduledRounds||'—')+' rounds</small>'+model(b)+'</div><div class="ksl-pfl-fightmarket"><span class="ksl-pfl-muted">No sportsbook-verified betting markets</span></div></article>').join(''):'<p class="ksl-pfl-muted">'+(only==='ready'?'No verified betting-ready fights currently available. Choose All fights to view the schedule.':'No upcoming scheduled fights match this view. Completed events are excluded.')+'</p>';
}
function hydrate(snapshot){
 if(!snapshot||!Array.isArray(snapshot.events))throw Error('Invalid event schedule');
 const next=snapshot.events.flatMap(e=>(e.bouts||[]).filter(b=>eligible(e,b)).map(b=>({...b,eventName:e.name,date:e.date})));
 bouts=next;hydrated=true;
 byId('fight-count').textContent=String(bouts.length);
 byId('fight-label').textContent='Upcoming scheduled bouts only';
 byId('ml-count').textContent='0';byId('totals-count').textContent='0';byId('edge-count').textContent='0';
 byId('feed-status').textContent='UPCOMING '+bouts.length+' · VERIFIED BOOK ODDS 0';
 render();
}
for(const id of ['fight-search','market','sort','only-ready'])byId(id)?.addEventListener('input',render);
fetch('./data/pfl/events.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(hydrate).catch(err=>{
 byId('feed-status').textContent='STATIC SCHEDULE · LIVE REFRESH UNAVAILABLE';
 byId('coverage-label').textContent='Schedule refresh failed: '+err.message+'; showing last published schedule if available.';
 // The HTML fallback is intentionally preserved.
});
if(window.KSLPFLFeed?.load)window.KSLPFLFeed.load().then(feed=>{enrichment=feed; if(hydrated)render();byId('history-state').textContent=feed.history?'HISTORY LOADED':'HISTORY UNAVAILABLE';byId('odds-state').textContent='0 VERIFIED';byId('sim-state').textContent=(feed.projections?.available||0)+' EXPLORATORY';}).catch(()=>{});
})();