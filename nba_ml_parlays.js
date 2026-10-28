(()=>{'use strict';
const status=document.getElementById('nba-ml-status'),out=document.getElementById('nba-ml-cards');if(!out)return;
const odds=p=>p<0?(-p)/(-p+100):100/(p+100);
const american=p=>p>=.5?'-'+Math.round(100*p/(1-p)):'+'+Math.round(100*(1-p)/p);
const dateET=d=>(()=>{const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(d));const get=k=>parts.find(x=>x.type===k).value;return get('year')+'-'+get('month')+'-'+get('day')})();

const node=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n};
async function refresh(){
 out.replaceChildren();status.textContent='Loading NBA moneyline research…';const today=dateET(Date.now());
 try{
 const resp=await fetch('./feed/basketball_nba.json?ml='+Date.now(),{cache:'no-store'});if(!resp.ok)throw Error('NBA odds feed HTTP '+resp.status);
 const data=await resp.json();if(data.status!=='ok'||data.sport!=='basketball_nba')throw Error('NBA odds feed invalid or degraded');const rows=Array.isArray(data.odds)?data.odds:[];const feedAge=Date.parse(data.fetched_at);if(!Number.isFinite(feedAge)||feedAge>Date.now()||Date.now()-feedAge>90*60000)throw Error('NBA odds snapshot stale or missing timestamp');
 const now=Date.now();const games=new Map();
 for(const r of rows){if(r.market!=='h2h'||!r.event_id||!r.bookmaker||!r.selection||!Number.isFinite(Number(r.price))||Number(r.price)===0)continue;
 const tip=Date.parse(r.commence_time);const updated=Date.parse(r.updated_at);if(!Number.isFinite(tip)||tip<=now||dateET(tip)!==today||!Number.isFinite(updated)||updated>now||now-updated>90*60000)continue;
 const key=String(r.event_id),group=games.get(key)||[];group.push(r);games.set(key,group);
 }
 const choices=[];const simulations=10000;const seeded=(seed)=>()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
 for(const [id,group] of games){const books=new Map();for(const r of group){const k=String(r.bookmaker);const a=books.get(k)||[];a.push(r);books.set(k,a)}
 let best=null;
 for(const [book,rs] of books){const sides=new Map();for(const r of rs)sides.set(String(r.selection),r);if(sides.size!==2)continue;const pair=[...sides.values()];if(pair.some(r=>r.event!==group[0].event))continue;const expected=String(group[0].event||'').split(' @ ');if(expected.length!==2||!pair.every(r=>expected.includes(String(r.selection))))continue;const duplicateSelection=rs.some(r=>rs.filter(x=>x.selection===r.selection).length>1);if(duplicateSelection)continue;const a=odds(Number(pair[0].price)),b=odds(Number(pair[1].price)),sum=a+b;if(sum<1||sum>1.2)continue;
 for(const r of pair){const p=odds(Number(r.price))/sum;const candidate={id,team:r.selection,book,price:Number(r.price),p,tip:r.commence_time};if(!best||candidate.p>best.p||(candidate.p===best.p&&candidate.book<best.book))best=candidate}}
 if(best)choices.push(best);
 }
 choices.sort((a,b)=>b.p-a.p);
 status.textContent='NBA ML Parlays · '+today+' ET · '+choices.length+' games with fresh two-sided quotes. No independent predictive model or verified EV available.';
 for(const [label,n] of [['Safer two-leg',2],['Balanced three-leg',3],['Four-leg',4],['Five-leg',5]]){
 const card=node('section','');card.style.cssText='border:1px solid #42677b;border-radius:12px;padding:14px;margin:12px 0;background:#10283a';card.append(node('h3',label));
 const byBook=new Map();for(const choice of choices){const group=byBook.get(choice.book)||[];group.push(choice);byBook.set(choice.book,group)}const eligibleBooks=[...byBook.entries()].filter(([,group])=>group.length>=n).sort((a,b)=>{const score=g=>g.slice(0,n).reduce((v,l)=>v*Math.max(.0001,l.p),1);return score(b[1])-score(a[1])});const legs=eligibleBooks.length?eligibleBooks[0][1].slice(0,n):[];if(legs.length<n){card.append(node('p','UNAVAILABLE — insufficient eligible games quoted by the SAME sportsbook'));out.append(card);continue}
 const ul=document.createElement('ul');let joint=1,decimal=1;const books=new Set(legs.map(x=>x.book));for(const l of legs){joint*=l.p;decimal*=l.price<0?1+100/-l.price:1+l.price/100;ul.append(node('li',l.team+' ML · '+l.book+' '+(l.price>0?'+':'')+l.price+' · no-vig market '+(100*l.p).toFixed(1)+'%'))}card.append(ul);
 const rand=seeded(2166136261+n);let successes=0;for(let i=0;i<simulations;i++){if(legs.every(l=>rand()<l.p))successes++}const mc=successes/simulations;
 card.append(node('p','10,000-draw independent-market Monte Carlo: '+(mc*100).toFixed(2)+'% (simulation of market-implied probabilities only; NOT an independently calibrated forecast).'));
 card.append(node('p','Model EV: UNAVAILABLE · requires independently validated probabilities and executable same-book parlay prices.'));
 card.append(node('p','Diamond grade: UNVERIFIED · injury, lineup, rest and calibration checks not complete.'));
 card.append(node('p',books.size===1?'All legs quoted at '+[...books][0]+'; combined odds are mathematical only, not a verified parlay offer.':'MIXED BOOKMAKERS — combined quoted odds are NOT a purchasable parlay.'));card.append(node('p','Illustrative independent-market product: '+(joint*100).toFixed(1)+'% · fair '+american(joint)+' · combined quoted '+american(1/decimal)+'. NOT a calibrated model probability, EV or verified sportsbook parlay quote.'));
 card.append(node('p','RESEARCH ONLY · lineup, injury, correlated outcomes, sportsbook parlay pricing and model calibration not validated.'));out.append(card);
 }
 if(!choices.length)out.append(node('p','No eligible same-day moneylines. Fresh paired bookmaker odds are required; no fabricated picks.'));
 }catch(err){status.textContent='UNAVAILABLE — '+err.message;out.append(node('p','No parlay recommendations without a valid odds feed.'))}
}
document.getElementById('nba-ml-refresh')?.addEventListener('click',refresh);refresh();
})();