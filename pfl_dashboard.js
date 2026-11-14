(function(){'use strict';
const $=id=>document.getElementById(id);let fights=[];
function safe(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function fighterName(f){return typeof f==='string'?f:(f?.name||f?.slug||'Unknown fighter')}
function validSnapshot(data){return data&&data.schemaVersion===1&&Array.isArray(data.events)&&typeof data.retrievedAt==='string'}
function ready(m){return !!(window.KSLPFLBets&&window.KSLPFLBets.assess(m).eligible)}
function normName(v){return String(v||'').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'').replace(/sergei/g,'sergey')}
function consensusIndex(feed){
 const index=new Map(),events=feed.snapshot?.events||[];
 for(const card of feed.consensus?.cards||[]){
  const oddsEvent=feed.consensus?.cards&&card.data?.event;
  const date=String(oddsEvent?.starts_at||oddsEvent?.date||'').slice(0,10);
  const sourceEvent=events.find(e=>date&&String(e.date).slice(0,10)===date);
  if(!sourceEvent)continue;
  for(const line of card.data?.fights||[]){
   const names=[line.fighter_a?.name,line.fighter_b?.name].map(normName);
   if(names.some(n=>!n))continue;
   const match=(sourceEvent.bouts||[]).filter(b=>{
    const fighters=(b.fighters||[]).map(x=>normName(fighterName(x)));
    return fighters.length===2&&fighters.every(n=>names.includes(n));
   });
   if(match.length!==1||!line.consensus)continue;
   const price=line.consensus;
   if(!Number.isFinite(price.a?.american)||!Number.isFinite(price.b?.american))continue;
   index.set(String(match[0].id),{a:price.a.american,b:price.b.american,first:line.fighter_a.name,second:line.fighter_b.name,recordedAt:price.recorded_at,sources:price.sources});
  }
 }
 return index;
}
function american(n){return (n>0?'+':'')+n}
function modelCard(f){
 const p=f.projection,valid=p&&p.available===true&&Number.isFinite(p.probabilityA)&&Number.isFinite(p.probabilityB)&&Math.abs(p.probabilityA+p.probabilityB-1)<.02&&Array.isArray(p.fighters)&&p.fighters.length===2;
 let winner='<div class="ksl-pfl-prediction-pending">MODEL WINNER: UNAVAILABLE <small>Insufficient verified fighter history</small></div>';
 if(valid){const a=p.probabilityA>=p.probabilityB,w=p.fighters[a?0:1],prob=a?p.probabilityA:p.probabilityB;winner='<div class="ksl-pfl-prediction-win"><span>MODEL PREDICTED WINNER · EXPLORATORY</span><strong>'+safe(fighterName(w).replace(/-/g,' '))+'</strong><small>'+ (prob*100).toFixed(1)+'% · 50K simulations · Not calibrated</small></div>';}
 const c=f.consensus;
 if(!valid&&c&&Number.isFinite(c.a)&&Number.isFinite(c.b)){const implied=n=>n<0?-n/(-n+100):100/(n+100),pa=implied(c.a),pb=implied(c.b),side=pa>=pb?c.first:c.second,prob=Math.max(pa,pb)/(pa+pb);winner='<div class="ksl-pfl-prediction-market"><span>CONSENSUS FAVORITE · NOT OUR MODEL PICK</span><strong>'+safe(side)+'</strong><small>'+(prob*100).toFixed(1)+'% no-vig market estimate · Unverified sportsbook</small></div>';}
 const t=f.roundProjection;
 let rounds='<div class="ksl-pfl-prediction-pending">TOTAL ROUNDS: NO MODEL RECOMMENDATION <small>Validated finish-time distribution unavailable</small></div>';
 if(!t&&Array.isArray(f.totalConsensus)&&f.totalConsensus.length){const v=f.totalConsensus[0],implied=n=>n<0?-n/(-n+100):100/(n+100);if(Number.isFinite(v.line)&&Number.isFinite(v.over?.american)&&Number.isFinite(v.under?.american)){const pa=implied(v.over.american),pb=implied(v.under.american),over=pa>=pb;rounds='<div class="ksl-pfl-prediction-market"><span>ROUNDS MARKET LEAN · NOT OUR MODEL PICK</span><strong>'+(over?'Over ':'Under ')+safe(v.line)+'</strong><small>'+(100*Math.max(pa,pb)/(pa+pb)).toFixed(1)+'% no-vig market estimate · Not verified</small></div>';}}
 if(t&&t.available===true&&t.modelCalibrated===true&&Number.isFinite(t.probability)&&t.probability>0&&t.probability<1&&Number.isFinite(t.line)&&['over','under'].includes(t.side)){rounds='<div class="ksl-pfl-prediction-win"><span>MODEL TOTAL ROUNDS</span><strong>'+safe(t.side.toUpperCase())+' '+safe(t.line)+'</strong><small>'+ (t.probability*100).toFixed(1)+'% · Calibrated</small></div>';}
 return '<div class="ksl-pfl-predictions">'+winner+rounds+'</div>';
}
function isUpcoming(f,now=new Date()){const day=String(f.date||'').slice(0,10),today=now.toISOString().slice(0,10);return f.status==='scheduled'&&f.eventStatus==='scheduled'&&/^\d{4}-\d{2}-\d{2}$/.test(day)&&day>=today&&!f.winnerFighterSlug&&!f.resultRound&&!f.method;}
function draw(){
const q=$('fight-search').value.toLowerCase().trim(),market=$('market').value,only=$('only-ready').value,sort=$('sort').value;
let rows=fights.filter(f=>isUpcoming(f)).filter(f=>[f.name,f.eventName,...(f.fighters||[]).map(fighterName)].join(' ').toLowerCase().includes(q)).filter(f=>only!=='ready'||(f.markets||[]).some(ready));
rows=rows.map(f=>({...f,markets:(f.markets||[]).filter(m=>market==='all'||m.market===market)}));
rows.sort((a,b)=>sort==='confidence'?(b.confidenceScore||0)-(a.confidenceScore||0):sort==='ev'?(b.bestEv??-Infinity)-(a.bestEv??-Infinity):String(a.date||'').localeCompare(String(b.date||'')));
$('fight-board').innerHTML=rows.length?rows.map(f=>'<article class="ksl-pfl-fight"><div><small class="ksl-pfl-eyebrow">'+safe(f.eventName||'PFL EVENT')+'</small><h3>'+safe((f.fighters||[]).map(fighterName).join(' vs ')||f.name||'Matchup pending')+'</h3>'+(f.consensus?'<p class="ksl-pfl-muted">Market consensus (not sportsbook odds): '+safe(f.consensus.first)+' '+american(f.consensus.a)+' / '+safe(f.consensus.second)+' '+american(f.consensus.b)+' · '+safe(f.consensus.recordedAt||'time unverified')+'</p>':'')+'<small class="ksl-pfl-muted">'+safe(f.date||'Date unverified')+' · '+safe(f.scheduledRounds||'—')+' rounds</small>' +modelCard(f)+'</div><div class="ksl-pfl-fightmarket">'+(f.markets.length?f.markets.map(m=>'<div><strong>'+safe(m.label||m.market)+'</strong><span>'+ (ready(m)?safe(m.odds)+' · '+Math.round(m.probability*100)+'% model':'UNVERIFIED')+'</span></div>').join('') :'<span class="ksl-pfl-muted">No verified betting markets</span>')+'</div></article>').join(''):'<p class="ksl-pfl-muted">No upcoming scheduled fights match these filters. Past fights are hidden from the betting board.</p>';
}
function load(data){
if(!validSnapshot(data))throw Error('Invalid snapshot schema');
const gate=window.KSLPFLSnapshot&&window.KSLPFLSnapshot.check(data);
if(!gate||!gate.ok){const issues=gate?.errors||['Snapshot validation unavailable'];if(issues.some(x=>!x.includes('older than 24 hours')))throw Error('Invalid event snapshot: '+issues.join('; '));}
const stale=Date.now()-Date.parse(data.retrievedAt)>24*3600000;
const events=data.events;fights=events.flatMap(e=>Array.isArray(e.bouts)?e.bouts.map(b=>({...b,eventName:e.name,date:e.date,eventStatus:e.status})):[]);
$('fight-count').textContent=fights.filter(isUpcoming).length||'0';$('fight-label').textContent='Upcoming scheduled bouts only';
$('ml-count').textContent=fights.reduce((n,f)=>n+(f.markets||[]).filter(m=>m.market==='ml'&&ready(m)).length,0);
$('totals-count').textContent=fights.reduce((n,f)=>n+(f.markets||[]).filter(m=>m.market==='total'&&ready(m)).length,0);
const markets=fights.flatMap(f=>(f.markets||[]).map(m=>({...m,fightId:m.fightId||f.id})));const ranked=window.KSLPFLBets.rank(markets);$('edge-count').textContent=ranked.filter(x=>x.assessment.positiveEV).length;$('edge-board').innerHTML=ranked.filter(x=>x.assessment.positiveEV).length?ranked.filter(x=>x.assessment.positiveEV).slice(0,10).map(x=>'<div class="ksl-pfl-fight"><div><strong>'+safe(x.market.selection)+'</strong><small class="ksl-pfl-muted"> '+safe(x.market.book)+' · '+safe(x.market.oddsTimestamp)+'</small></div><div><strong>EV '+(x.assessment.ev*100).toFixed(1)+'%</strong><small>Fair '+x.assessment.fairOdds+'</small></div></div>').join(''):'No verified positive-EV PFL bets available.';$('feed-status').textContent='ODDS PENDING · MODEL PENDING';
$('card-state').textContent=stale?'SCHEDULE STALE':'UNVERIFIED';draw();
}
['fight-search','market','sort','only-ready'].forEach(id=>$(id).addEventListener('input',draw));
window.KSLPFLFeed.load().then(feed=>{
 if(!feed.snapshot)throw Error('Event snapshot not published');
 load(feed.snapshot);
 const stale=Date.now()-Date.parse(feed.snapshot.retrievedAt)>24*3600000;
 const byFight=new Map();
 for(const m of feed.markets){const key=String(m.fightId);if(!byFight.has(key))byFight.set(key,[]);byFight.get(key).push(m)}
 for(const fight of fights){fight.markets=byFight.get(String(fight.id))||[]}
 const consensus=feed.matchedConsensus?.rows?new Map(feed.matchedConsensus.rows.map(r=>[String(r.fightId),{first:r.markets[0].selection,a:r.markets[0].american,second:r.markets[1].selection,b:r.markets[1].american,recordedAt:r.recordedAt,sources:r.sources}])):consensusIndex(feed);const matched=new Map((feed.matchedConsensus?.rows||[]).map(r=>[String(r.fightId),r]));for(const fight of fights){fight.consensus=stale?null:(consensus.get(String(fight.id))||null);fight.totalConsensus=stale?[]:(matched.get(String(fight.id))?.totalRounds||[]);}
 const projected=new Map((feed.projections?.bouts||[]).filter(b=>b.available).map(b=>[String(b.boutId),b]));
 for(const fight of fights){fight.projection=projected.get(String(fight.id))||null;if(stale)fight.markets=[];}
 const verifiedBouts=feed.boutReadiness?.identityAndHistoryVerified??0;
 $('history-state').textContent=feed.history?'HISTORICAL FEATURES LOADED':'NOT PUBLISHED';
 $('card-state').textContent=verifiedBouts+' BOUTS VERIFIED';
 $('odds-state').textContent=feed.markets.filter(ready).length+' BETTING-ELIGIBLE MARKETS';
 $('sim-state').textContent=(feed.projections?.available||0)+'/'+(feed.projections?.bouts?.length||0)+' SIMULATED · MODEL PENDING';
 $('feed-status').textContent=(stale?'STALE SCHEDULE · ':'')+'UPCOMING '+fights.filter(isUpcoming).length+' · VERIFIED BOOK ODDS '+(stale?0:feed.markets.length);
 $('ml-count').textContent=feed.markets.filter(m=>m.market==='ml'&&ready(m)).length;
 $('totals-count').textContent=feed.markets.filter(m=>m.market==='total'&&ready(m)).length;
 $('edge-count').textContent=window.KSLPFLBets.rank(feed.markets).filter(x=>x.assessment.positiveEV).length;
 $('coverage-label').textContent=(stale?'Event schedule snapshot is older than 24 hours; refresh required before betting. ':'')+verifiedBouts+' identity/history-verified bouts; '+(feed.projections?.available||0)+' historical simulations; '+feed.markets.length+' validated markets. Betting eligibility requires calibrated simulations and live odds.';
 draw();
}).catch(async e=>{
 $('feed-status').textContent='FEED DEGRADED · SCHEDULE FALLBACK';
 try{
  const r=await fetch('./data/pfl/events.json',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);
  const snapshot=await r.json();if(!validSnapshot(snapshot))throw Error('Invalid event data');
  fights=snapshot.events.flatMap(event=>(event.bouts||[]).map(b=>({...b,eventName:event.name,date:event.date,eventStatus:event.status,markets:[]})));
  $('fight-count').textContent=fights.filter(isUpcoming).length;
  $('fight-label').textContent='Upcoming scheduled bouts · fallback';
  $('ml-count').textContent='0';$('totals-count').textContent='0';$('edge-count').textContent='0';
  $('coverage-label').textContent='Fallback schedule only. Predictions and odds are unavailable until the full feed is restored.';
  $('feed-status').textContent='SCHEDULE ONLY · ODDS UNAVAILABLE';
  draw();
 }catch(fallbackError){$('fight-board').textContent='PFL schedule unavailable: '+fallbackError.message+' (initial feed: '+e.message+')';}
});
})();