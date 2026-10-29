(()=>{'use strict';
const status=document.getElementById('nba-ml-status'),out=document.getElementById('nba-ml-cards');if(!out)return;
const odds=p=>p<0?(-p)/(-p+100):100/(p+100);
const decimalPrice=price=>price<0?1+100/-price:1+price/100;
const estimatedEV=(prob,price)=>prob*decimalPrice(price)-1;
const american=p=>p>=.5?'-'+Math.round(100*p/(1-p)):'+'+Math.round(100*(1-p)/p);
const dateET=d=>(()=>{const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(d));const get=k=>parts.find(x=>x.type===k).value;return get('year')+'-'+get('month')+'-'+get('day')})();

const node=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n};
async function refresh(){
 out.replaceChildren();status.textContent='Loading NBA moneyline research…';const today=dateET(Date.now());
 try{
 const resp=await fetch('./feed/basketball_nba.json?ml='+Date.now(),{cache:'no-store'});if(!resp.ok)throw Error('NBA odds feed HTTP '+resp.status);
 const data=await resp.json();if(data.status!=='ok'||data.sport!=='basketball_nba')throw Error('NBA odds feed invalid or degraded');const rows=Array.isArray(data.odds)?data.odds:[];const feedAge=Date.parse(data.fetched_at);if(!Number.isFinite(feedAge)||feedAge>Date.now()||Date.now()-feedAge>150*60000){const age=Number.isFinite(feedAge)?Math.round((Date.now()-feedAge)/60000):null;status.textContent='NBA ML PARLAYS · ODDS FEED STALE · NOT BET ELIGIBLE';out.append(node('p','Last published sportsbook snapshot: '+(Number.isFinite(feedAge)?new Date(feedAge).toLocaleString('en-US',{timeZone:'America/New_York',dateStyle:'medium',timeStyle:'short',timeZoneName:'short'}):'timestamp missing')+(age===null?'':' · '+age+' minutes old')+'.'));const scheduled=new Map();for(const r of rows){if(r.market!=='h2h'||!r.event_id||!r.commence_time||Date.parse(r.commence_time)<=Date.now())continue;const key=String(r.event_id);if(!scheduled.has(key))scheduled.set(key,r)}if(scheduled.size){out.append(node('p','Previously captured upcoming games (schedule reference only; prices are stale):'));const ul=node('ul','');for(const r of [...scheduled.values()].sort((a,b)=>Date.parse(a.commence_time)-Date.parse(b.commence_time)).slice(0,20))ul.append(node('li',String(r.event||r.event_id)+' · '+new Date(r.commence_time).toLocaleString('en-US',{timeZone:'America/New_York',weekday:'short',hour:'numeric',minute:'2-digit',timeZoneName:'short'})));out.append(ul)}else out.append(node('p','No upcoming games in the last published snapshot.'));out.append(node('p','No picks or parlays are issued from stale odds. Reloading this page cannot refresh the upstream sportsbook feed.'));return;}
 const readinessResponse=await fetch('./feed/nba_ml_betting_readiness.json?ml='+Date.now(),{cache:'no-store'});
 if(!readinessResponse.ok)throw Error('NBA moneyline readiness report unavailable; fail closed');
 const readiness=await readinessResponse.json();
 const required=['odds_fresh','model_fresh_and_calibrated','schedule_evidence_fresh','pregame_odds_archiving_active','historical_pregame_odds_backtest','closing_line_value_verified','injury_lineup_rest_confirmed','executable_same_book_parlay_quote','correlation_stress_test_verified'];
 const ready=readiness.status==='bet_eligible'&&required.every(k=>readiness.checks?.[k]===true);
 if(!ready){status.textContent='NBA ML PARLAYS · RESEARCH ONLY · NOT BET ELIGIBLE';out.append(node('p','Automatic parlay recommendations are disabled until all independent validation, lineup, pricing and correlation checks pass.'));out.append(node('p','Outstanding: '+required.filter(k=>readiness.checks?.[k]!==true).join(', ')));return;}
 const now=Date.now();const games=new Map();
 let model=new Map(),modelState='UNAVAILABLE';
 try{
  const mr=await fetch('./feed/nba_ml_predictions.json?ml='+Date.now(),{cache:'no-store'});
  if(mr.ok){const m=await mr.json();const age=Date.parse(m.generated_at);
   if(m.status==='validated'&&m.sport==='basketball_nba'&&m.calibration_passed===true&&Number.isFinite(age)&&age<=now&&now-age<=150*60000&&Array.isArray(m.predictions)){
    for(const p of m.predictions){if(!p.event_id||!p.team||!Number.isFinite(p.win_probability)||p.win_probability<=0||p.win_probability>=1||p.date_et!==today)continue;model.set(String(p.event_id)+'|'+String(p.team),p.win_probability)}
    modelState=model.size?'VALIDATED':'UNAVAILABLE';
   }
  }
 }catch(_){modelState='UNAVAILABLE'}

 for(const r of rows){if(r.market!=='h2h'||!r.event_id||!r.bookmaker||!r.selection||!Number.isFinite(Number(r.price))||Number(r.price)===0)continue;
 const tip=Date.parse(r.commence_time);const updated=Date.parse(r.updated_at);if(!Number.isFinite(tip)||tip<=now||dateET(tip)!==today||!Number.isFinite(updated)||updated>now||now-updated>150*60000)continue;
 const key=String(r.event_id),group=games.get(key)||[];group.push(r);games.set(key,group);
 }
 const choices=[];const simulations=10000;const seeded=(seed)=>()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
 for(const [id,group] of games){const books=new Map();for(const r of group){const k=String(r.bookmaker);const a=books.get(k)||[];a.push(r);books.set(k,a)}
 for(const [book,rs] of books){const sides=new Map();for(const r of rs)sides.set(String(r.selection),r);if(sides.size!==2)continue;const pair=[...sides.values()];if(pair.some(r=>r.event!==group[0].event))continue;const expected=String(group[0].event||'').split(' @ ');if(expected.length!==2||!pair.every(r=>expected.includes(String(r.selection))))continue;const duplicateSelection=rs.some(r=>rs.filter(x=>x.selection===r.selection).length>1);if(duplicateSelection)continue;const a=odds(Number(pair[0].price)),b=odds(Number(pair[1].price)),sum=a+b;if(sum<1||sum>1.2)continue;
 for(const r of pair){const p=odds(Number(r.price))/sum;const mp=model.get(id+'|'+String(r.selection));const candidate={id,team:r.selection,book,price:Number(r.price),p,mp,ev:Number.isFinite(mp)?estimatedEV(mp,Number(r.price)):null,tip:r.commence_time};choices.push(candidate)}}
 }
 choices.sort((a,b)=>b.p-a.p);
 status.textContent='NBA ML Parlays · '+today+' ET · '+games.size+' games with fresh two-sided quotes · Independent model: '+modelState+' · BETTING READINESS: NOT VERIFIED.';
 for(const [label,n] of [['Safer two-leg',2],['Balanced three-leg',3],['Four-leg',4],['Five-leg',5]]){
 const card=node('section','');card.style.cssText='border:1px solid #42677b;border-radius:12px;padding:14px;margin:12px 0;background:#10283a';card.append(node('h3',label));
 const byBook=new Map();for(const choice of choices){const group=byBook.get(choice.book)||[];group.push(choice);byBook.set(choice.book,group)}for(const group of byBook.values()){group.sort((a,b)=>{return (b.ev??-Infinity)-(a.ev??-Infinity)||b.p-a.p});const seen=new Set();for(let i=0;i<group.length;){if(seen.has(group[i].id))group.splice(i,1);else{seen.add(group[i].id);i++}}}const eligibleBooks=[...byBook.entries()].filter(([,group])=>group.filter(l=>Number.isFinite(l.ev)&&l.ev>0).length>=n).map(([book,group])=>[book,group.filter(l=>Number.isFinite(l.ev)&&l.ev>0)]).sort((a,b)=>{const score=g=>g.slice(0,n).reduce((v,l)=>v*decimalPrice(l.price)*l.mp,1);return score(b[1])-score(a[1])});const legs=eligibleBooks.length?eligibleBooks[0][1].slice(0,n):[];if(legs.length<n){card.append(node('p','UNAVAILABLE — insufficient positive-model-EV games quoted by the SAME sportsbook; no fallback to market-only picks'));out.append(card);continue}
 const ul=document.createElement('ul');let joint=1,decimal=1;const books=new Set(legs.map(x=>x.book));for(const l of legs){joint*=l.p;decimal*=l.price<0?1+100/-l.price:1+l.price/100;ul.append(node('li',l.team+' ML · '+l.book+' '+(l.price>0?'+':'')+l.price+' · model '+(100*l.mp).toFixed(1)+'% · no-vig '+(100*l.p).toFixed(1)+'% · single-leg EV '+(100*l.ev).toFixed(1)+'%'))}card.append(ul);
 const modelPs=legs.map(l=>model.get(l.id+'|'+l.team));const hasModel=modelPs.every(p=>Number.isFinite(p)&&p>0&&p<1);const rand=seeded(2166136261+n);let successes=0;for(let i=0;i<simulations;i++){if(legs.every((l,k)=>rand()<(hasModel?modelPs[k]:l.p)))successes++}const mc=successes/simulations;const se=Math.sqrt(mc*(1-mc)/simulations);
 card.append(node('p',hasModel?'10,000-draw independently calibrated model Monte Carlo: '+(mc*100).toFixed(2)+'% (95% simulation interval ±'+(196*se).toFixed(2)+' percentage points; assumes independent games, correlation unverified).':'10,000-draw independent-market Monte Carlo: '+(mc*100).toFixed(2)+'% (market-implied probabilities only; NOT an independently calibrated forecast).'));
 card.append(node('p',hasModel?'Illustrative model EV (UNVERIFIED parlay quote): '+((modelPs.reduce((a,b)=>a*b,1)*decimal-1)*100).toFixed(1)+'% · NOT BET ELIGIBLE until executable parlay odds and correlation are verified.':'Model EV: UNAVAILABLE · requires independently validated probabilities and executable same-book parlay prices.'));
 card.append(node('p','Diamond grade: UNVERIFIED · injury, lineup, rest, historical price backtest, correlation and executable pricing checks not complete.'));
 card.append(node('p',books.size===1?'All legs quoted at '+[...books][0]+'; combined odds are mathematical only, not a verified parlay offer.':'MIXED BOOKMAKERS — combined quoted odds are NOT a purchasable parlay.'));card.append(node('p','Illustrative independent-market product: '+(joint*100).toFixed(1)+'% · fair '+american(joint)+' · combined quoted '+american(1/decimal)+'. NOT a calibrated model probability, EV or verified sportsbook parlay quote.'));
 card.append(node('p','RESEARCH ONLY · positive estimated single-leg EV is not verified profit; no confirmed injury/lineup feed, closing-line backtest, correlated outcomes or executable sportsbook parlay quote.'));out.append(card);
 }
 if(!choices.length)out.append(node('p','No eligible same-day moneylines. Fresh paired bookmaker odds are required; no fabricated picks.'));
 }catch(err){status.textContent='UNAVAILABLE — '+err.message;out.append(node('p','No parlay recommendations without a valid odds feed.'))}
}
document.getElementById('nba-ml-refresh')?.addEventListener('click',refresh);refresh();
})();