(()=>{'use strict';
const status=document.getElementById('nba-ml-status'),out=document.getElementById('nba-ml-cards');if(!out)return;
const odds=p=>p<0?(-p)/(-p+100):100/(p+100);
const american=p=>p>=.5?'-'+Math.round(100*p/(1-p)):'+'+Math.round(100*(1-p)/p);
const dateET=d=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(d));
const today=dateET(Date.now());
const node=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n};
async function refresh(){
 out.replaceChildren();status.textContent='Loading NBA moneyline research…';
 try{
 const resp=await fetch('./data/nba_props.json?ml='+Date.now(),{cache:'no-store'});if(!resp.ok)throw Error('NBA odds feed HTTP '+resp.status);
 const data=await resp.json();const rows=Array.isArray(data)?data:Array.isArray(data.rows)?data.rows:Array.isArray(data.odds)?data.odds:[];
 const now=Date.now();const games=new Map();
 for(const r of rows){if(r.market!=='h2h'||!r.event_id||!r.bookmaker||!r.selection||!Number.isFinite(Number(r.price))||Number(r.price)===0)continue;
 const tip=Date.parse(r.commence_time);const updated=Date.parse(r.updated_at);if(!Number.isFinite(tip)||tip<=now||dateET(tip)!==today||!Number.isFinite(updated)||updated>now||now-updated>90*60000)continue;
 const key=String(r.event_id),group=games.get(key)||[];group.push(r);games.set(key,group);
 }
 const choices=[];
 for(const [id,group] of games){const books=new Map();for(const r of group){const k=String(r.bookmaker);const a=books.get(k)||[];a.push(r);books.set(k,a)}
 let best=null;
 for(const [book,rs] of books){const sides=new Map();for(const r of rs)sides.set(String(r.selection),r);if(sides.size!==2)continue;const pair=[...sides.values()],a=odds(Number(pair[0].price)),b=odds(Number(pair[1].price)),sum=a+b;if(sum<=0||sum>1.35)continue;
 for(const r of pair){const p=odds(Number(r.price))/sum;const candidate={id,team:r.selection,book,price:Number(r.price),p,tip:r.commence_time};if(!best||candidate.p>best.p)best=candidate}}
 if(best)choices.push(best);
 }
 choices.sort((a,b)=>b.p-a.p);
 status.textContent='NBA ML Parlays · '+today+' ET · '+choices.length+' games with fresh two-sided quotes. No independent predictive model or verified EV available.';
 for(const [label,n] of [['Safer two-leg',2],['Balanced three-leg',3],['Four-leg',4],['Five-leg',5]]){
 const card=node('section','');card.style.cssText='border:1px solid #42677b;border-radius:12px;padding:14px;margin:12px 0;background:#10283a';card.append(node('h3',label));
 const legs=choices.slice(0,n);if(legs.length<n){card.append(node('p','UNAVAILABLE — insufficient eligible games'));out.append(card);continue}
 const ul=document.createElement('ul');let joint=1,decimal=1;for(const l of legs){joint*=l.p;decimal*=l.price<0?1+100/-l.price:1+l.price/100;ul.append(node('li',l.team+' ML · '+l.book+' '+(l.price>0?'+':'')+l.price+' · no-vig market '+(100*l.p).toFixed(1)+'%'))}card.append(ul);
 card.append(node('p','Illustrative independent-market product: '+(joint*100).toFixed(1)+'% · fair '+american(joint)+' · combined quoted '+american(1/decimal)+'. NOT model probability, Monte Carlo, EV or a verified book parlay quote.'));
 card.append(node('p','RESEARCH ONLY · lineup, injury, correlated outcomes, sportsbook parlay pricing and model calibration not validated.'));out.append(card);
 }
 if(!choices.length)out.append(node('p','No eligible same-day moneylines. Fresh paired bookmaker odds are required; no fabricated picks.'));
 }catch(err){status.textContent='UNAVAILABLE — '+err.message;out.append(node('p','No parlay recommendations without a valid odds feed.'))}
}
document.getElementById('nba-ml-refresh')?.addEventListener('click',refresh);refresh();
})();