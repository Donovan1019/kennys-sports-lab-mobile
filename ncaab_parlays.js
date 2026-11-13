/* NCAA cross-game moneyline parlay price board: arithmetic only, not a prediction. */
(function(){
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
const decimal=p=>{const n=Number(p);return !Number.isFinite(n)||n===0?null:n>0?1+n/100:1+100/-n};
const american=d=>d>=2?'+'+Math.round((d-1)*100):String(Math.round(-100/(d-1)));
const etDate=value=>{const p=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value)).split('/');return p[2]+'-'+p[0].padStart(2,'0')+'-'+p[1].padStart(2,'0')};
const ev=(probability,dec)=>Number.isFinite(probability)&&probability>=0&&probability<=1&&Number.isFinite(dec)&&dec>1?probability*(dec-1)-(1-probability):null;
function render(events,date,meta,projections,research){
 const age=Date.now()-Date.parse(meta?.fetched_at||'');
 if(!Number.isFinite(age)||age<0||age>21600000)return '<div class="panel">UNAVAILABLE — NCAA sportsbook prices are missing or more than six hours old.</div>';
 const byBook=new Map();
 for(const e of events||[]){
  const start=Date.parse(e.commence_time);
  if(!Number.isFinite(start)||start<=Date.now()||etDate(e.commence_time)!==date)continue;
  for(const b of e.bookmakers||[]){
   const bookAge=Date.now()-Date.parse(b.last_update||'');
   if(!Number.isFinite(bookAge)||bookAge<0||bookAge>21600000)continue;
   const m=(b.markets||[]).find(x=>x.key==='h2h');
   if(!m)continue;
   const candidates=(m.outcomes||[]).filter(o=>(o.name===e.home_team||o.name===e.away_team)&&decimal(o.price)!==null);
   if(new Set(candidates.map(o=>o.name)).size!==2)continue;
   if(candidates.length!==2)continue;
   const fav=candidates.slice().sort((a,b)=>decimal(a.price)-decimal(b.price))[0];
   const list=byBook.get(b.key||b.title)||[];
   list.push({event:e.id||e.home_team+'|'+e.away_team,game:e.away_team+' @ '+e.home_team,selection:fav.name,price:fav.price,dec:decimal(fav.price),book:b.title,start});
   byBook.set(b.key||b.title,list);
  }
 }
 const model=window.NCAABProbability;
 const audit=model?model.audit(research):{ready:false,reason:'MODEL_NOT_LOADED'};
 const cards=[];
 for(const [key,legs] of byBook){
  const unique=[...new Map(legs.map(l=>[l.event,l])).values()].sort((a,b)=>a.start-b.start||a.game.localeCompare(b.game));
  if(unique.length<2)continue;
  // A deterministic same-book cross-game two-leg quote, not a recommended selection.
  const pair=unique.slice(0,2),combined=pair.reduce((v,l)=>v*l.dec,1);
  cards.push('<article class="game"><strong>'+esc(pair[0].book)+' · 2-game ML price example</strong>'+pair.map(l=>'<div class="sgp-leg"><span>'+esc(l.game)+' · '+esc(l.selection)+'</span><strong>'+esc(l.price>0?'+'+l.price:l.price)+'</strong></div>').join('')+'<div class="meta">Calculated parlay price: '+esc(american(combined))+' · implied break-even: '+(100/combined).toFixed(1)+'% · NOT a model probability</div></article>');
 }
 const eligible=Number(projections?.coverage?.eligible_teams||0),observed=Number(projections?.coverage?.observed_teams||0);const reasons=projections?.coverage?.ineligible_reasons||{};
 const insufficient=Number(reasons.insufficient_current_season_games);
 const provisional=Object.keys(projections?.coverage?.provisional_teams||{}).length;
 const coverageDetail=Number.isFinite(insufficient)?' · Teams below five current-season games: '+esc(insufficient):' · Current-season five-game eligibility gate is active';
 const calibrationDetail=audit.reason==='INDEPENDENT_CALIBRATION_REQUIRED'?' · Historical backtest is not an independently calibrated probability model.':'';
 const readiness='<div class="panel"><strong>Kenny model readiness: '+esc(audit.reason)+'</strong><p>Walk-forward evaluations: '+esc(research?.walk_forward?.games||0)+' / 200 minimum · Eligible teams: '+esc(eligible)+' / '+esc(observed)+' observed'+coverageDetail+' · Provisional research teams: '+esc(provisional)+'. '+(audit.ready?'Calibrated model available.':'No model-approved parlays until independent calibration and eligible team matchups are verified.')+calibrationDetail+'</p></div>';
 return '<h2>NCAA Moneyline Parlays · Market Research</h2>'+readiness+'<div class="panel"><strong>PRICE EXAMPLES ONLY · NOT BETTING-READY</strong><p>Two upcoming games, same sportsbook, moneyline favorites. Sorted by scheduled start time. Arithmetic prices are indicative; actual sportsbook parlay acceptance, price, settlement and Onyx availability are unverified. No simulations, calibrated joint probabilities or EV.</p></div>'+(cards.length?cards.join(''):'<div class="panel">UNAVAILABLE — fewer than two verified same-day moneylines from a single sportsbook.</div>');
}
window.NCAABParlays={render,decimal,american,ev};
})();
