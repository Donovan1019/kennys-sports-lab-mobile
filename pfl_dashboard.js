(function(){'use strict';
const $=id=>document.getElementById(id);let fights=[];
function safe(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function fighterName(f){return typeof f==='string'?f:(f?.name||f?.slug||'Unknown fighter')}
function validSnapshot(data){return data&&data.schemaVersion===1&&Array.isArray(data.events)&&typeof data.retrievedAt==='string'}
function ready(m){return !!(window.KSLPFLBets&&window.KSLPFLBets.assess(m).eligible)}
function draw(){
const q=$('fight-search').value.toLowerCase().trim(),market=$('market').value,only=$('only-ready').value,sort=$('sort').value;
let rows=fights.filter(f=>[f.name,f.eventName,...(f.fighters||[]).map(fighterName)].join(' ').toLowerCase().includes(q)).filter(f=>only!=='ready'||(f.markets||[]).some(ready));
rows=rows.map(f=>({...f,markets:(f.markets||[]).filter(m=>market==='all'||m.market===market)})).filter(f=>market==='all'||f.markets.length);
rows.sort((a,b)=>sort==='confidence'?(b.confidenceScore||0)-(a.confidenceScore||0):sort==='ev'?(b.bestEv??-Infinity)-(a.bestEv??-Infinity):String(a.date||'').localeCompare(String(b.date||'')));
$('fight-board').innerHTML=rows.length?rows.map(f=>'<article class="ksl-pfl-fight"><div><small class="ksl-pfl-eyebrow">'+safe(f.eventName||'PFL EVENT')+'</small><h3>'+safe((f.fighters||[]).map(fighterName).join(' vs ')||f.name||'Matchup pending')+'</h3><small class="ksl-pfl-muted">'+safe(f.date||'Date unverified')+' · '+safe(f.scheduledRounds||'—')+' rounds</small>'+(f.projection?'<p class="ksl-pfl-muted">Exploratory 50k simulation: '+safe(f.projection.fighters[0])+' '+(f.projection.probabilityA*100).toFixed(1)+'% / '+safe(f.projection.fighters[1])+' '+(f.projection.probabilityB*100).toFixed(1)+'% · NOT CALIBRATED</p>':'')+'</div><div class="ksl-pfl-fightmarket">'+(f.markets.length?f.markets.map(m=>'<div><strong>'+safe(m.label||m.market)+'</strong><span>'+ (ready(m)?safe(m.odds)+' · '+Math.round(m.probability*100)+'% model':'UNVERIFIED')+'</span></div>').join('') :'<span class="ksl-pfl-muted">No verified betting markets</span>')+'</div></article>').join(''):'<p class="ksl-pfl-muted">No matching verified fight records. Change filters or await an authorized event feed.</p>';
}
function load(data){
if(!validSnapshot(data))throw Error('Invalid snapshot schema');
const gate=window.KSLPFLSnapshot&&window.KSLPFLSnapshot.check(data);
if(!gate||!gate.ok)throw Error('Snapshot provenance or freshness verification failed');
const events=data.events;fights=events.flatMap(e=>Array.isArray(e.bouts)?e.bouts.map(b=>({...b,eventName:e.name,date:e.date})):[]);
$('fight-count').textContent=fights.length||'—';$('fight-label').textContent=fights.length?'Snapshot bouts (not betting-ready)':'Event metadata only';
$('ml-count').textContent=fights.reduce((n,f)=>n+(f.markets||[]).filter(m=>m.market==='ml'&&ready(m)).length,0);
$('totals-count').textContent=fights.reduce((n,f)=>n+(f.markets||[]).filter(m=>m.market==='total'&&ready(m)).length,0);
const markets=fights.flatMap(f=>(f.markets||[]).map(m=>({...m,fightId:m.fightId||f.id})));const ranked=window.KSLPFLBets.rank(markets);$('edge-count').textContent=ranked.filter(x=>x.assessment.positiveEV).length;$('edge-board').innerHTML=ranked.filter(x=>x.assessment.positiveEV).length?ranked.filter(x=>x.assessment.positiveEV).slice(0,10).map(x=>'<div class="ksl-pfl-fight"><div><strong>'+safe(x.market.selection)+'</strong><small class="ksl-pfl-muted"> '+safe(x.market.book)+' · '+safe(x.market.oddsTimestamp)+'</small></div><div><strong>EV '+(x.assessment.ev*100).toFixed(1)+'%</strong><small>Fair '+x.assessment.fairOdds+'</small></div></div>').join(''):'No verified positive-EV PFL bets available.';$('feed-status').textContent='RESEARCH SNAPSHOT · ODDS UNVERIFIED';
$('card-state').textContent='UNVERIFIED';draw();
}
['fight-search','market','sort','only-ready'].forEach(id=>$(id).addEventListener('input',draw));
window.KSLPFLFeed.load().then(feed=>{
 if(!feed.snapshot)throw Error('Event snapshot not published');
 load(feed.snapshot);
 const byFight=new Map();
 for(const m of feed.markets){const key=String(m.fightId);if(!byFight.has(key))byFight.set(key,[]);byFight.get(key).push(m)}
 for(const fight of fights){fight.markets=byFight.get(String(fight.id))||[]}
 const projected=new Map((feed.projections?.bouts||[]).filter(b=>b.available).map(b=>[String(b.boutId),b]));
 for(const fight of fights){fight.projection=projected.get(String(fight.id))||null;}
 const verifiedBouts=feed.boutReadiness?.identityAndHistoryVerified??0;
 $('history-state').textContent=feed.history?'HISTORICAL FEATURES LOADED':'NOT PUBLISHED';
 $('card-state').textContent=verifiedBouts+' BOUTS VERIFIED';
 $('odds-state').textContent=feed.markets.length+' VERIFIED MARKETS';
 $('sim-state').textContent=(feed.projections?.available||0)+' EXPLORATORY · UNCALIBRATED';
 $('feed-status').textContent='FIGHTS '+fights.length+' · VERIFIED ODDS '+feed.markets.length;
 $('ml-count').textContent=feed.markets.filter(m=>m.market==='ml').length;
 $('totals-count').textContent=feed.markets.filter(m=>m.market==='total').length;
 $('coverage-label').textContent=verifiedBouts+' identity/history-verified bouts; '+feed.markets.length+' validated markets. Betting eligibility requires calibrated simulations.';
 draw();
}).catch(e=>{fights=[];$('feed-status').textContent='SNAPSHOT NOT PUBLISHED';$('fight-board').textContent='No published PFL snapshot available: '+e.message;});
})();