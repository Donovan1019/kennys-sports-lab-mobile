/* NCAA exact-market break-even audit. No unsupported model win probabilities. */
(function(){
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const implied=p=>{const n=Number(p);return !Number.isFinite(n)||n===0?null:n<0?-n/(-n+100):100/(n+100)};
const american=p=>{const n=Number(p);return n>0?'+'+n:String(n)};
function render(events,date){
 const rows=[];
 for(const event of events||[]){
  const d=new Date(event.commence_time);
  if(Number.isNaN(d.getTime())||new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(d)!==date)continue;
  for(const book of event.bookmakers||[]){
   for(const market of book.markets||[]){
    if(!['h2h','spreads','totals'].includes(market.key))continue;
    for(const o of market.outcomes||[]){
     const p=implied(o.price);
     if(p===null)continue;
     rows.push({game:event.away_team+' @ '+event.home_team,book:book.title,market:market.key,selection:o.name,point:o.point,price:o.price,breakEven:p});
    }
   }
  }
 }
 rows.sort((a,b)=>a.game.localeCompare(b.game)||a.market.localeCompare(b.market)||a.breakEven-b.breakEven);
 const games=new Map();
 for(const row of rows){const list=games.get(row.game)||[];list.push(row);games.set(row.game,list)}
 return '<h2>Betting Decision Board ('+games.size+' games)</h2><div class="panel"><strong>LIVE-PRICE RESEARCH — MODEL EDGE NOT VERIFIED</strong><p>Exact sportsbook odds and break-even probability are shown. No EV, win probability, confidence or Diamond selection is claimed without calibrated model probabilities. Same-line price comparison does not imply a positive expected value.</p></div>'+(games.size?[...games].map(([game,rs])=>'<article class="game"><strong>'+esc(game)+'</strong>'+rs.slice(0,40).map(r=>'<div class="sgp-leg"><span>'+esc(r.book)+' · '+esc(r.market.toUpperCase())+' · '+esc(r.selection)+(r.point==null?'':' '+esc(r.point))+'</span><span>'+esc(american(r.price))+' · '+(r.breakEven*100).toFixed(1)+'% BE</span></div>').join('')+'<div class="meta">Verdict: NO VERIFIED EDGE · simulation calibration pending</div></article>').join(''):'<div class="panel">UNAVAILABLE — no verified, current odds for this date.</div>');
}
window.NCAABDecision={render,implied};
})();