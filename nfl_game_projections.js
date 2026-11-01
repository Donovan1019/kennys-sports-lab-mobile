/* Game-level NFL projections integrated inside Player Projections. No synthetic bookmaker lines. */
(()=>{'use strict';if(window.KSL_ACTIVE_SPORT!=='NFL')return;
const root=document.getElementById('ksl-stat-root');if(!root)return;
const section=document.createElement('section');section.setAttribute('aria-label','NFL game and period projections');section.style.cssText='border:1px solid #45687d;border-radius:12px;padding:14px;margin:16px 0';
const title=document.createElement('h2');title.textContent='🏈 Game & Period Projections · Model Estimates';section.append(title);
const note=document.createElement('p');note.textContent='Inside the projection model: team-scoring simulations, not player-stat extrapolations. Full-game estimates are experimental; period markets require verified historical period scoring. No invented sportsbook prices.';section.append(note);
const market=document.createElement('select');market.setAttribute('aria-label','Game projection market');const period=document.createElement('select');period.setAttribute('aria-label','Game projection period');const matchup=document.createElement('select');matchup.setAttribute('aria-label','Game projection matchup');
for(const x of [market,period,matchup])x.style.cssText='padding:10px;margin:5px 6px 5px 0;max-width:100%;background:#10283a;color:white;border:1px solid #42677b;border-radius:8px';
for(const x of ['Moneyline','Spread','Game Total','Team Total']){const o=document.createElement('option');o.textContent=x;market.append(o)}
for(const x of ['Full game','1st half','2nd half','1st quarter','2nd quarter','3rd quarter','4th quarter']){const o=document.createElement('option');o.textContent=x;period.append(o)}
section.append(market,period,matchup);const status=document.createElement('p');const output=document.createElement('div');section.append(status,output);
const attachToProjectionPanel=()=>{const playerBox=Array.from(document.querySelectorAll('section')).find(x=>x.querySelector('h2')?.textContent?.includes('Player Projections · Model Estimates'));if(!playerBox)return false;playerBox.id='nfl-player-projections';section.id='nfl-game-projections';const playerMarket=playerBox.querySelector('select[aria-label="Projection market"]');if(playerMarket&&section.parentNode!==playerBox)playerBox.insertBefore(section,playerMarket);else if(!playerMarket&&section.parentNode!==playerBox)playerBox.append(section);return true};if(!attachToProjectionPanel()){const observer=new MutationObserver(()=>{if(attachToProjectionPanel())observer.disconnect()});observer.observe(document.body,{childList:true,subtree:true})}
let games=[],quotes=[],oddsCheckedAt=null,oddsError='';const clean=x=>String(x||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const isRegular=x=>{const d=new Date(x.date);return Number.isFinite(d.getTime())&&d.getUTCMonth()!==7&&d.getTime()<Date.now()};
const history=t=>(t?.score_history||[]).filter(x=>isRegular(x)&&Number.isFinite(Number(x.scored))&&Number.isFinite(Number(x.allowed))).slice(0,12);
const mean=x=>x.reduce((a,b)=>a+b,0)/x.length;
const seedRand=key=>{let state=Array.from(key).reduce((h,c)=>(Math.imul(h,1664525)+c.charCodeAt(0)+1013904223)>>>0,2166136261)||1;return()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return (state+.5)/4294967296}};
const pct=(x,p)=>x[Math.max(0,Math.min(x.length-1,Math.floor(p*(x.length-1))))];
function simulation(g){const away=g.teams?.find(t=>clean(t.team)===clean(g.away)),home=g.teams?.find(t=>clean(t.team)===clean(g.home));const ah=history(away),hh=history(home);if(ah.length<8||hh.length<8)return null;
const af=mean(ah.map(x=>Number(x.scored))),aa=mean(ah.map(x=>Number(x.allowed))),hf=mean(hh.map(x=>Number(x.scored))),ha=mean(hh.map(x=>Number(x.allowed)));
const aMean=(af+ha)/2,hMean=(hf+aa)/2;
const rand=seedRand(g.event_id||g.event),draws=[];let aWins=0,hWins=0,ties=0;
for(let i=0;i<10000;i++){const ar=ah[Math.floor(rand()*ah.length)],hr=hh[Math.floor(rand()*hh.length)];const as=Math.max(0,aMean+.5*(Number(ar.scored)-af)+.5*(Number(hr.allowed)-ha));const hs=Math.max(0,hMean+.5*(Number(hr.scored)-hf)+.5*(Number(ar.allowed)-aa));draws.push({away:as,home:hs,total:as+hs,margin:hs-as});if(hs>as)hWins++;else if(as>hs)aWins++;else ties++}
const range=k=>{const x=draws.map(d=>d[k]).sort((a,b)=>a-b);return {mid:pct(x,.5),low:pct(x,.1),high:pct(x,.9)}};
return {aMean,hMean,away:range('away'),home:range('home'),total:range('total'),margin:range('margin'),aWins,hWins,ties,draws,n:draws.length,ah:ah.length,hh:hh.length}}
const row=(label,value)=>{const d=document.createElement('div');d.style.cssText='display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid #29475b;flex-wrap:wrap';const l=document.createElement('span');l.textContent=label;const v=document.createElement('strong');v.textContent=value;d.append(l,v);return d};
const fmt=x=>Number(x).toFixed(1);
const american=p=>p>0?'+'+p:String(p);
const decimal=p=>p>0?1+p/100:1+100/Math.abs(p);
const fair=p=>p>0&&p<1?(p>=.5?'-'+Math.round(100*p/(1-p)):'+'+Math.round(100*(1-p)/p)):'unavailable';
const timeET=x=>new Date(x).toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})+' ET';
const sportsbookLine=(g,kind)=>{const rows=matchQuotes(g,kind);const first=rows.find(q=>q.bookmaker==='draftkings'&&Number.isFinite(q.point))||rows.find(q=>q.bookmaker==='fanduel'&&Number.isFinite(q.point));if(!first)return null;if(kind==='spreads'){const home=clean(first.selection)===clean(g.home);const away=clean(first.selection)===clean(g.away);if(!home&&!away)return null;return {line:home?first.point:-first.point,book:first.bookmaker,updated_at:first.updated_at}}if(kind==='totals')return {line:first.point,book:first.bookmaker,updated_at:first.updated_at};return null};
const matchEvent=(q,g)=>clean(q.event)===clean(g.event)&&Math.abs(Date.parse(q.commence_time)-Date.parse(g.commence_time))<=600000;
const isFresh=(q,g)=>matchEvent(q,g)&&['draftkings','fanduel'].includes(String(q.bookmaker).toLowerCase())&&Number.isFinite(q.price)&&Math.abs(q.price)>=100&&Number.isFinite(Date.parse(q.updated_at))&&Date.parse(q.updated_at)<=Date.now()+60000&&Date.now()-Date.parse(q.updated_at)<=21600000&&Date.parse(g.commence_time)>Date.now();
const matchQuotes=(g,m)=>quotes.filter(q=>isFresh(q,g)&&q.market===m);
function oddsRows(card,g,sim){
 const kind=market.value==='Moneyline'?'h2h':market.value==='Spread'?'spreads':market.value==='Game Total'?'totals':null;
 if(!kind){card.append(row('DK/FD','No verified team-total quote integration'));return}
 const matching=matchQuotes(g,kind);let shown=0;
 for(const book of ['draftkings','fanduel']){
 const selection=matching.filter(q=>q.bookmaker===book);
 for(const q of selection){
 let p=null,push=0,point='';
 if(kind==='h2h'){if(![g.away,g.home].some(x=>clean(x)===clean(q.selection)))continue;p=clean(q.selection)===clean(g.home)?sim.hWins/sim.n:sim.aWins/sim.n;push=sim.ties/sim.n}
 if(kind==='spreads'){if(!Number.isFinite(q.point)||![g.away,g.home].some(x=>clean(x)===clean(q.selection)))continue;const home=clean(q.selection)===clean(g.home);p=sim.draws.filter(d=>(home?d.margin:-d.margin)+q.point>0).length/sim.n;push=sim.draws.filter(d=>(home?d.margin:-d.margin)+q.point===0).length/sim.n;point=' '+(q.point>0?'+':'')+q.point}
 if(kind==='totals'){if(!Number.isFinite(q.point)||!['over','under'].includes(String(q.selection).toLowerCase()))continue;const over=String(q.selection).toLowerCase()==='over';p=sim.draws.filter(d=>over?d.total>q.point:d.total<q.point).length/sim.n;push=sim.draws.filter(d=>d.total===q.point).length/sim.n;point=' '+q.point}
 if(p===null)continue;
 const ev=p*(decimal(q.price)-1)-(1-p-push);
 card.append(row(book.toUpperCase()+' · '+q.selection+point,american(q.price)+' · '+timeET(q.updated_at)));
 card.append(row('Model probability / push',fmt(p*100)+'% / '+fmt(push*100)+'%'));
 card.append(row('Model fair odds (push excluded)',fair(p/(1-push))));
 card.append(row('Research EV / unit',fmt(ev*100)+'% · NOT BET ELIGIBLE'));shown++;
 }}
 if(!shown)card.append(row('DraftKings / FanDuel',oddsError?'Feed error: '+oddsError:'No verified current matching '+kind+' quote'+(oddsCheckedAt?' · checked '+timeET(oddsCheckedAt):' · feed not checked')));
}
function verdict(card,g,sim){
 const kind=market.value==='Moneyline'?'h2h':market.value==='Spread'?'spreads':market.value==='Game Total'?'totals':null;
 const panel=document.createElement('section');panel.setAttribute('aria-label','Final verdict model prediction');panel.style.cssText='border:2px solid #2bbf72;background:#103b2b;color:#e7fff0;border-radius:12px;padding:14px;margin:16px 0';
 const heading=document.createElement('h3');heading.textContent='FINAL VERDICT / MODEL PREDICTION';heading.style.color='#83f4b2';panel.append(heading);
 const message=s=>{const p=document.createElement('p');p.textContent=s;panel.append(p)};
 const candidates=[];
 if(kind)for(const q of matchQuotes(g,kind)){
  let probability=null,push=0,selection='';
  if(kind==='h2h'){
   if(![g.home,g.away].some(t=>clean(t)===clean(q.selection)))continue;
   probability=clean(q.selection)===clean(g.home)?sim.hWins/sim.n:sim.aWins/sim.n;
   push=sim.ties/sim.n;selection=q.selection+' ML';
  }else if(kind==='spreads'){
   if(!Number.isFinite(q.point)||![g.home,g.away].some(t=>clean(t)===clean(q.selection)))continue;
   const home=clean(q.selection)===clean(g.home);
   probability=sim.draws.filter(d=>(home?d.margin:-d.margin)+q.point>0).length/sim.n;
   push=sim.draws.filter(d=>(home?d.margin:-d.margin)+q.point===0).length/sim.n;
   selection=q.selection+' '+(q.point>0?'+':'')+q.point;
  }else if(kind==='totals'){
   if(!Number.isFinite(q.point)||!['over','under'].includes(String(q.selection).toLowerCase()))continue;
   const over=String(q.selection).toLowerCase()==='over';
   probability=sim.draws.filter(d=>over?d.total>q.point:d.total<q.point).length/sim.n;
   push=sim.draws.filter(d=>d.total===q.point).length/sim.n;
   selection=q.selection+' '+q.point;
  }
  if(probability===null||probability+push>1.00001)continue;
  const ev=probability*(decimal(q.price)-1)-(1-probability-push);
  candidates.push({selection,book:q.bookmaker,price:q.price,probability,push,ev,updated:q.updated_at});
 }
 candidates.sort((a,b)=>b.ev-a.ev||b.probability-a.probability);
 const best=candidates[0];
 if(!best)message('PASS - No verified current matching sportsbook quote for this market.');
 else if(best.ev<=0)message('PASS - No positive research-model edge at verified sportsbook prices.');
 else{
  message('Research model lean: '+best.selection+' / '+best.book.toUpperCase()+' '+american(best.price));
  panel.append(row('Model probability / push',fmt(best.probability*100)+'% / '+fmt(best.push*100)+'%'));
  panel.append(row('Model fair odds',fair(best.probability/(1-best.push))));
  panel.append(row('Research EV / unit',fmt(best.ev*100)+'%'));
  panel.append(row('Quote time',timeET(best.updated)));
 }
 message('NOT BET ELIGIBLE - Experimental historical bootstrap; calibration and injury/lineup checks unavailable.');
 card.append(panel);
}
async function loadOdds(){
 try{const r=await fetch('./feed/americanfootball_nfl.json?projection_odds='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(!Array.isArray(d.odds))throw Error('invalid feed');quotes=d.odds;oddsError='';oddsCheckedAt=Date.now()}
 catch(e){quotes=[];oddsError=e.message;oddsCheckedAt=Date.now()}draw()
}
function draw(){output.replaceChildren();const g=games.find(x=>x.event_id===matchup.value);if(!g){status.textContent='No upcoming scheduled matchup with verified team inputs';return}
const card=document.createElement('article');card.style.cssText='border:1px solid #45687d;border-radius:12px;padding:14px;background:#10283a;margin-top:12px';
const h=document.createElement('h3');h.textContent=g.away+' @ '+g.home;card.append(h);
const label=period.value+' · '+market.value;card.append(row('Market',label));
if(period.value!=='Full game'){card.append(row('Projection','Awaiting verified period-by-period historical scoring data'),row('Simulation','Not run — full-game scores cannot validate quarter/half forecasts'),row('DK/FD','No verified current period lines in connected feed'));status.textContent='Period market selected · data integrity gate';output.append(card);return}
const sim=simulation(g);if(!sim){card.append(row('Projection','Insufficient verified regular-season team scoring history'),row('Simulation','Unavailable'));status.textContent='Historical data integrity gate';output.append(card);return}
status.textContent='10,000 game-level bootstrap simulations · '+sim.ah+' away-team and '+sim.hh+' home-team historical games · experimental';
if(market.value==='Moneyline'){card.append(row(g.home+' win simulation',fmt(100*sim.hWins/sim.n)+'%'),row(g.away+' win simulation',fmt(100*sim.aWins/sim.n)+'%'),row('Simulated ties',fmt(100*sim.ties/sim.n)+'%'))}
if(market.value==='Spread'){const bookLine=sportsbookLine(g,'spreads');const line=bookLine?bookLine.line:NaN;if(!Number.isFinite(line))card.append(row('Spread probabilities','No verified current DK/FD spread'));else{card.append(row('Automatic home spread',String(line)+' · '+bookLine.book.toUpperCase()+' · '+timeET(bookLine.updated_at)));const cover=sim.draws.filter(d=>d.margin+line>0).length, push=sim.draws.filter(d=>d.margin+line===0).length;card.append(row('Home projected margin',fmt(sim.hMean-sim.aMean)),row('80% simulated home margin',fmt(sim.margin.low)+' to '+fmt(sim.margin.high)),row(g.home+' '+(line>0?'+':'')+line+' covers',fmt(100*cover/sim.n)+'%'),row(g.away+' '+(line<0?'+':'')+(-line)+' covers',fmt(100*(sim.n-cover-push)/sim.n)+'%'),row('Spread push',fmt(100*push/sim.n)+'%'))}}
if(market.value==='Game Total'){const bookLine=sportsbookLine(g,'totals');const line=bookLine?bookLine.line:NaN;if(!Number.isFinite(line)||line<=0)card.append(row('Total probabilities','No verified current DK/FD total'));else{card.append(row('Automatic game total',String(line)+' · '+bookLine.book.toUpperCase()+' · '+timeET(bookLine.updated_at)));const over=sim.draws.filter(d=>d.total>line).length,push=sim.draws.filter(d=>d.total===line).length;card.append(row('Projected total',fmt(sim.aMean+sim.hMean)),row('80% simulated total',fmt(sim.total.low)+' to '+fmt(sim.total.high)),row('Over '+line,fmt(100*over/sim.n)+'%'),row('Under '+line,fmt(100*(sim.n-over-push)/sim.n)+'%'),row('Total push',fmt(100*push/sim.n)+'%'))}}
if(market.value==='Team Total'){card.append(row(g.away+' projected points',fmt(sim.aMean)),row(g.away+' 80% range',fmt(sim.away.low)+' to '+fmt(sim.away.high)),row(g.home+' projected points',fmt(sim.hMean)),row(g.home+' 80% range',fmt(sim.home.low)+' to '+fmt(sim.home.high)))}
oddsRows(card,g,sim);verdict(card,g,sim);card.append(row('Validation','EXPERIMENTAL · not calibrated · no injury/starting-lineup verification'));output.append(card)}
for(const x of [market,period,matchup])x.addEventListener('change',draw);const refresh=document.createElement('button');refresh.type='button';refresh.textContent='Refresh DK/FD published odds';refresh.addEventListener('click',loadOdds);section.insertBefore(refresh,status);loadOdds();
fetch('./feed/independent_game_inputs.json?game_projection='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('inputs unavailable');return r.json()}).then(d=>{games=(d.games||[]).filter(g=>Date.parse(g.commence_time)>Date.now()&&Array.isArray(g.teams)&&g.teams.length===2).sort((a,b)=>Date.parse(a.commence_time)-Date.parse(b.commence_time));for(const g of games){const o=document.createElement('option');o.value=g.event_id;o.textContent=g.event;matchup.append(o)}draw()}).catch(()=>{status.textContent='Independent team scoring feed unavailable; projections disabled'});
})();
