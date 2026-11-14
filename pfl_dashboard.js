(function(){'use strict';
const $=id=>document.getElementById(id);let fights=[];
function safe(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function validSnapshot(data){return data&&data.schemaVersion===1&&Array.isArray(data.events)&&typeof data.retrievedAt==='string'}
function ready(m){return m&&m.verified===true&&m.fresh===true&&m.calibrated===true&&m.simulated===true&&Number.isFinite(m.odds)&&Number.isFinite(m.probability)}
function draw(){
const q=$('fight-search').value.toLowerCase().trim(),market=$('market').value,only=$('only-ready').value,sort=$('sort').value;
let rows=fights.filter(f=>[f.name,f.eventName,...(f.fighters||[])].join(' ').toLowerCase().includes(q)).filter(f=>only!=='ready'||(f.markets||[]).some(ready));
rows=rows.map(f=>({...f,markets:(f.markets||[]).filter(m=>market==='all'||m.market===market)})).filter(f=>market==='all'||f.markets.length);
rows.sort((a,b)=>sort==='confidence'?(b.confidenceScore||0)-(a.confidenceScore||0):sort==='ev'?(b.bestEv??-Infinity)-(a.bestEv??-Infinity):String(a.date||'').localeCompare(String(b.date||'')));
$('fight-board').innerHTML=rows.length?rows.map(f=>'<article class="ksl-pfl-fight"><div><small class="ksl-pfl-eyebrow">'+safe(f.eventName||'PFL EVENT')+'</small><h3>'+safe((f.fighters||[]).join(' vs ')||f.name||'Matchup pending')+'</h3><small class="ksl-pfl-muted">'+safe(f.date||'Date unverified')+' · '+safe(f.scheduledRounds||'—')+' rounds</small></div><div class="ksl-pfl-fightmarket">'+(f.markets.length?f.markets.map(m=>'<div><strong>'+safe(m.label||m.market)+'</strong><span>'+ (ready(m)?safe(m.odds)+' · '+Math.round(m.probability*100)+'% model':'UNVERIFIED')+'</span></div>').join(''):'<span class="ksl-pfl-muted">No verified betting markets</span>')+'</div></article>').join(''):'<p class="ksl-pfl-muted">No matching verified fight records. Change filters or await an authorized event feed.</p>';
}
function load(data){
if(!validSnapshot(data))throw Error('Invalid snapshot schema');
const gate=window.KSLPFLSnapshot&&window.KSLPFLSnapshot.check(data);
if(!gate||!gate.ok)throw Error('Snapshot provenance or freshness verification failed');
const events=data.events;fights=events.flatMap(e=>Array.isArray(e.bouts)?e.bouts.map(b=>({...b,eventName:e.name,date:e.date})):[]);
$('fight-count').textContent=fights.length||'—';$('fight-label').textContent=fights.length?'Snapshot bouts (not betting-ready)':'Event metadata only';
$('ml-count').textContent=fights.reduce((n,f)=>n+(f.markets||[]).filter(m=>m.market==='ml'&&ready(m)).length,0);
$('totals-count').textContent=fights.reduce((n,f)=>n+(f.markets||[]).filter(m=>m.market==='total'&&ready(m)).length,0);
$('edge-count').textContent='—';$('feed-status').textContent='RESEARCH SNAPSHOT · ODDS UNVERIFIED';
$('card-state').textContent='UNVERIFIED';draw();
}
['fight-search','market','sort','only-ready'].forEach(id=>$(id).addEventListener('input',draw));
fetch('./data/pfl/events.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Snapshot not published');return r.json()}).then(load).catch(()=>{fights=[];$('feed-status').textContent='DATA UNAVAILABLE';draw()});
})();