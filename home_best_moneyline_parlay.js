/* Kenny's verified cross-sport moneyline parlay — no sportsbook-derived predictions. */
(()=>{'use strict';
const root=document.getElementById('ksl-best-ml-parlay');if(!root)return;
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const decimal=o=>o>0?1+o/100:1+100/(-o);
const american=d=>d>=2?'+'+Math.round((d-1)*100):'-'+Math.round(100/(d-1));
const age=t=>Date.now()-Date.parse(t);
const verified=r=>r&&r.market==='ML'&&r.data_status==='VERIFIED'&&r.simulation_status==='COMPLETE'&&r.price_verified===true&&Number.isInteger(r.simulations)&&r.simulations>=10000&&Number.isFinite(r.model_probability)&&r.model_probability>0&&r.model_probability<1&&Number.isFinite(r.odds)&&Math.abs(r.odds)>=100&&r.odds!==0&&r.model_source&& !['sportsbook','implied_odds'].includes(String(r.model_source).toLowerCase())&&r.selection&&r.event&&r.sport&&r.source&&['CONFIRMED','VERIFIED'].includes(r.lineup_status)&&age(r.odds_timestamp)>=0&&age(r.odds_timestamp)<=15*60000&&age(r.model_generated_at)>=0&&age(r.model_generated_at)<=60*60000&&Date.parse(r.start_time)>Date.now();
root.innerHTML='<div class="kml-head"><div><h2>🏆 Best Moneyline Parlay · All Sports</h2><p>Verified picks prioritized · research clearly labeled · +100 minimum · Monte Carlo</p></div><button id="kml-refresh" type="button">↻ Refresh</button></div><p id="kml-status" role="status">Checking Kenny’s model…</p><div id="kml-ticket"></div><p class="kml-note">One selection per game. Independent cross-game simulation; correlation calibration pending. Never substitute market-implied probabilities for model projections.</p>';
const status=document.getElementById('kml-status'),ticket=document.getElementById('kml-ticket'),button=document.getElementById('kml-refresh');
function best(rows){
 const unique=new Map();
 for(const r of rows.filter(verified)){const key=String(r.sport)+'|'+String(r.event_id||r.event);const old=unique.get(key)||[];old.push(r);unique.set(key,old)}
 const groups=[...unique.values()].map(a=>a.sort((x,y)=>y.model_probability*decimal(y.odds)-x.model_probability*decimal(x.odds)).slice(0,3));
 let winner=null;
 function visit(i,legs,d,p){if(legs.length>=2&&d>=2&&legs.every(r=>r.source===legs[0].source)){const ev=p*d-1;if(ev>0&&(!winner||p>winner.p+1e-9||(Math.abs(p-winner.p)<1e-9&&ev>winner.ev)))winner={legs:[...legs],d,p,ev};}
 if(i>=groups.length||legs.length>=5)return;
 visit(i+1,legs,d,p);
 for(const r of groups[i])if(!legs.length||r.source===legs[0].source)visit(i+1,[...legs,r],d*decimal(r.odds),p*r.model_probability);
 }
 // Limit search to highest-value 9 distinct events to keep mobile responsive.
 const limited=groups.sort((a,b)=>Math.max(...b.map(r=>r.model_probability))-Math.max(...a.map(r=>r.model_probability))).slice(0,9);
 groups.length=0;groups.push(...limited);visit(0,[],1,1);return winner;
}
function simulate(legs,n=50000){let wins=0;for(let i=0;i<n;i++){let hit=true;for(const r of legs){if(Math.random()>=r.model_probability){hit=false;break}}if(hit)wins++}return {wins,n,p:wins/n}}
async function researchPreview(){
 const paths=['basketball_nba','icehockey_nhl','basketball_ncaab'];
 const loaded=await Promise.all(paths.map(async sport=>{
  try{
   const [odds,model]=await Promise.all([fetch('./feed/'+sport+'.json?ts='+Date.now(),{cache:'no-store'}),fetch('./feed/'+(sport==='basketball_nba'?'nba':sport==='icehockey_nhl'?'nhl':'ncaab')+'_ml_predictions.json?ts='+Date.now(),{cache:'no-store'})]);
   if(!odds.ok||!model.ok)return null;
   return {sport,odds:await odds.json(),model:await model.json()};
  }catch{return null}
 }));
 const now=Date.now(),groups=new Map(),candidates=[];
 for(const entry of loaded){
  if(!entry)continue;
  const {sport,odds,model}=entry;
  if(odds.status!=='ok'||(sport==='basketball_nba'?(model.status!=='validated'||model.calibration_passed!==true):sport==='icehockey_nhl'?model.status!=='RESEARCH_ONLY':model.status!=='RESEARCH_ONLY'))continue;
  const generated=Date.parse(model.generated_at),fetched=Date.parse(odds.fetched_at);
  if(!Number.isFinite(generated)||!Number.isFinite(fetched)||now-generated<0||now-generated>150*60000||now-fetched<0||now-fetched>15*60000)continue;
  const predictions=new Map();
  for(const p of model.predictions||[]){
   if((sport==='basketball_nba'||sport==='basketball_ncaab')&&p.event_id&&p.team&&Number.isFinite(p.win_probability))predictions.set(p.event_id+'|'+p.team,p.win_probability);
   if(sport==='icehockey_nhl'&&p.event_id&&p.event&&p.event.includes(' @ ')){
    const [away,home]=p.event.split(' @ ');
    if(Number.isFinite(p.away_win_probability))predictions.set(p.event_id+'|'+away,p.away_win_probability);
    if(Number.isFinite(p.home_win_probability))predictions.set(p.event_id+'|'+home,p.home_win_probability);
   }
  }
  for(const q of odds.odds||[]){
   const updated=Date.parse(q.updated_at);
   if(q.market!=='h2h'||!['fanduel','draftkings'].includes(q.bookmaker)||Date.parse(q.commence_time)<=now||!Number.isFinite(updated)||now-updated<0||now-updated>15*60000)continue;
   const p=predictions.get(q.event_id+'|'+q.selection);
   if(!(p>0&&p<1)||!Number.isFinite(q.price)||Math.abs(q.price)<100)continue;
   const key=q.bookmaker+'|'+sport+'|'+q.event_id,arr=groups.get(key)||[];
   arr.push({...q,p,sport});groups.set(key,arr);
  }
 }
 for(const arr of groups.values()){
  if(arr.length!==2||new Set(arr.map(q=>q.selection)).size!==2)continue;
  for(const q of arr)if(q.p*decimal(q.price)>1)candidates.push(q);
 }
 let best=null;
 for(const book of ['fanduel','draftkings']){
  const list=candidates.filter(q=>q.bookmaker===book).sort((a,b)=>(b.p*decimal(b.price)-1)-(a.p*decimal(a.price)-1)).slice(0,24);
  function walk(i,legs,d,p){
   if(legs.length>=2&&d>=2&&p*d>1&&(!best||(p*d-1)>best.ev+1e-9||(Math.abs((p*d-1)-best.ev)<1e-9&&p>best.p)))best={legs:[...legs],d,p,ev:p*d-1,book};
   if(i>=list.length||legs.length>=5)return;
   walk(i+1,legs,d,p);
   if(!legs.some(x=>x.sport===list[i].sport&&x.event_id===list[i].event_id))walk(i+1,[...legs,list[i]],d*decimal(list[i].price),p*list[i].p);
  }
  if(list.length)walk(0,[],1,1);
 }
 if(best){
  const n=50000;let wins=0;for(let i=0;i<n;i++)if(best.legs.every(r=>Math.random()<r.p))wins++;
  status.textContent='RESEARCH ONLY — '+n.toLocaleString()+' independent Monte Carlo trials · NOT BET-ELIGIBLE';
  ticket.innerHTML='<div class="kml-summary"><strong>'+american(best.d)+'</strong><span>Simulated win '+(wins/n*100).toFixed(1)+'%</span><span>Book '+esc(best.book)+'</span><span>Estimated EV '+((best.p*best.d-1)*100).toFixed(1)+'%</span></div>'+
   best.legs.map(r=>'<div class="kml-leg"><b>'+esc(r.selection)+'</b><span>'+esc(r.sport==='basketball_nba'?'NBA':r.sport==='basketball_ncaab'?'NCAAB':'NHL')+' · '+esc(r.event)+'</span><span>'+esc(r.price>0?'+'+r.price:r.price)+' · Research model '+(r.p*100).toFixed(1)+'%</span></div>').join('')+
   '<p class="kml-note"><strong>NOT A VERIFIED BET.</strong> NBA holdout is not approved for betting; NHL goalie and calibration inputs are unverified. Cross-game outcomes sampled independently; prices are individual legs, not a confirmed executable parlay quote. Research-only EV may be unreliable.</p>';
  return true;
 }
 if(!candidates.length)return false;
 const singles=candidates.sort((a,b)=>(b.p*decimal(b.price)-1)-(a.p*decimal(a.price)-1)).slice(0,5);
 status.textContent='RESEARCH ONLY — '+singles.length+' positive-model-EV moneylines; no qualifying +100 parlay';
 ticket.innerHTML=singles.map(r=>'<div class="kml-leg"><b>'+esc(r.selection)+'</b><span>'+esc(r.sport==='basketball_nba'?'NBA':r.sport==='basketball_ncaab'?'NCAAB':'NHL')+' · '+esc(r.event)+'</span><span>'+esc(r.bookmaker)+' '+esc(r.price>0?'+'+r.price:r.price)+' · Model '+(r.p*100).toFixed(1)+'% · estimated EV '+((r.p*decimal(r.price)-1)*100).toFixed(1)+'%</span></div>').join('')+
  '<p class="kml-note"><strong>NOT BET-ELIGIBLE.</strong> NBA holdout, injury and lineup checks and NHL goalie and calibration checks remain unverified. Historical NBA paper ROI was negative. Research-only EV is not a validated edge.</p>';
 return true;
}
async function refresh(){
 button.disabled=true;status.textContent='Loading verified Kenny’s model feed…';ticket.replaceChildren();
 try{const response=await fetch('./data/market_edges.json?ts='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error('Verified feed unavailable');const payload=await response.json(),rows=Array.isArray(payload)?payload:payload.edges;
 if(!Array.isArray(rows))throw Error('Invalid verified market feed');
 const eligible=rows.filter(verified),pick=best(eligible);
 if(!pick){if(await researchPreview().catch(()=>false))return;status.textContent='UNAVAILABLE — '+esc(payload.reason||'No qualified +100 parlay with verified inputs')+'; no fresh research alternative.';return}
 const mc=simulate(pick.legs),simEV=mc.p*pick.d-1;
 status.textContent='COMPLETE · '+mc.n.toLocaleString()+' Monte Carlo trials · '+pick.legs.length+' verified legs';
 ticket.innerHTML='<div class="kml-summary"><strong>'+american(pick.d)+'</strong><span>Simulated win '+(mc.p*100).toFixed(1)+'%</span><span>Model fair '+american(1/pick.p)+'</span><span>Simulated EV '+(simEV*100).toFixed(1)+'%</span></div>'+
 pick.legs.map(r=>'<div class="kml-leg"><b>'+esc(r.selection)+'</b><span>'+esc(r.sport)+' · '+esc(r.event)+'</span><span>'+esc(r.odds>0?'+'+r.odds:r.odds)+' · Kenny’s '+(r.model_probability*100).toFixed(1)+'% · '+r.simulations.toLocaleString()+' source simulations</span></div>').join('')+
 '<div class="kml-stake"><label>Stake $ <input id="kml-stake" type="number" min="1" value="25"></label><span id="kml-return"></span></div><small>Monte Carlo 95% sampling margin ±'+(196*Math.sqrt(mc.p*(1-mc.p)/mc.n)).toFixed(2)+' percentage points · independently sampled games · updated '+new Date().toLocaleTimeString()+'</small>';
 const stake=document.getElementById('kml-stake'),out=document.getElementById('kml-return');const calc=()=>{const x=Math.max(0,Number(stake.value)||0);out.textContent='Return $'+(x*pick.d).toFixed(2)+' · Profit $'+(x*(pick.d-1)).toFixed(2)};stake.addEventListener('input',calc);calc();
 }catch(e){if(!await researchPreview().catch(()=>false))status.textContent='UNAVAILABLE — '+String(e.message||'Verified feed could not be loaded');}
 finally{button.disabled=false}
}
button.addEventListener('click',refresh);refresh();
})();