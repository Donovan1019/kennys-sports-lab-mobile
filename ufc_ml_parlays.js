(()=>{'use strict';
const byId=id=>document.getElementById(id),status=byId('ufc-ml-status'),root=byId('ufc-ml-results'),btn=byId('ufc-ml-refresh'),legs=byId('ufc-ml-legs');if(!root)return;
const norm=x=>String(x||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9 ]/g,'').replace(/\s+/g,' ').trim();
const implied=p=>p<0?-p/(-p+100):100/(p+100);
const american=p=>p>=2?'+'+Math.round((p-1)*100):'-'+Math.round(100/(p-1));
const stamp=x=>{let n=Date.parse(x);return Number.isFinite(n)?new Date(n).toLocaleString('en-US',{timeZone:'America/New_York',dateStyle:'medium',timeStyle:'short'}):'unverified'};
const text=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n};
async function json(path){const r=await fetch(path+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(path+' HTTP '+r.status);return r.json()}
let saved=[];
function draw(){root.replaceChildren();const n=Number(legs.value);const books=['draftkings','fanduel'];let total=0;
for(const book of books){const picks=saved.filter(x=>x.book===book).sort((a,b)=>b.novig-a.novig).slice(0,n);if(picks.length<n)continue;
const card=text('article','');card.style.cssText='border:1px solid #42677b;border-radius:12px;padding:16px;margin:12px 0;background:#10283a';card.append(text('h3',n+'-fighter · '+book.toUpperCase()+' · RESEARCH ONLY'));const ul=document.createElement('ul');picks.forEach(p=>ul.append(text('li',p.name+' ML · '+(p.price>0?'+':'')+p.price+' · market no-vig '+(p.novig*100).toFixed(1)+'%')));card.append(ul);
const decimal=picks.reduce((v,p)=>v*(p.price>0?1+p.price/100:1+100/-p.price),1);card.append(text('p','Illustrative combined quoted odds: '+american(decimal)+' (saved snapshot only; NOT executable)'));
card.append(text('p','Independent fighter model: UNAVAILABLE · Monte Carlo: UNAVAILABLE · correlation: UNVERIFIED · parlay EV: UNAVAILABLE · NOT BET ELIGIBLE'));root.append(card);total++}
if(!total)root.append(text('p','No valid same-book '+n+'-fighter combination in the latest saved data. No parlay recommendations.'))}
async function load(){btn.disabled=true;status.textContent='Checking current UFC card and published DK/FD prices…';root.replaceChildren();saved=[];try{
const [card,feed]=await Promise.all([json('./feed/ufc_research.json'),json('./feed/mma_mixed_martial_arts.json')]);if(!Array.isArray(card.fights)||!Array.isArray(feed.odds)||feed.status!=='ok'||feed.source!=='the-odds-api-v4')throw Error('Invalid UFC data schema');
const now=Date.now(),snapshot=Date.parse(feed.fetched_at);if(!Number.isFinite(snapshot)||snapshot>now||now-snapshot>15*60000){status.textContent='STALE UFC ODDS · snapshot '+stamp(feed.fetched_at)+'. New sportsbook feed required. No betting-ready parlays.';draw();return}
const valid=card.fights.filter(f=>f.red&&f.blue&&Date.parse(f.start_time)>now);const groups=new Map();
for(const q of feed.odds){if(q.market!=='h2h'||!['draftkings','fanduel'].includes(q.bookmaker)||!q.event_id||!q.selection||!Number.isFinite(q.price)||(q.price>-100&&q.price<100)||Date.parse(q.commence_time)<=now||now-Date.parse(q.updated_at)>15*60000||Date.parse(q.updated_at)>now||Date.parse(q.updated_at)>snapshot||Date.parse(q.commence_time)<=snapshot)continue;const key=q.bookmaker+'|'+q.event_id;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(q)}
for(const [key,rows] of groups){const names=new Set(rows.map(q=>norm(q.selection)));if(names.size!==2)continue;const fight=valid.find(f=>names.has(norm(f.red))&&names.has(norm(f.blue))&&Math.abs(Date.parse(f.start_time)-Date.parse(rows[0].commence_time))<=90*60000);if(!fight)continue;
const pair=rows.filter(q=>q.commence_time===rows[0].commence_time);if(pair.length!==2||new Set(pair.map(q=>norm(q.selection))).size!==2||Math.abs(Date.parse(pair[0].updated_at)-Date.parse(pair[1].updated_at))>15*60000)continue;const sum=pair.reduce((v,q)=>v+implied(q.price),0);if(sum<1||sum>1.35)continue;
const fav=pair.sort((a,b)=>implied(b.price)-implied(a.price))[0];saved.push({book:fav.bookmaker,name:fav.selection,price:fav.price,novig:implied(fav.price)/sum,eventId:fav.event_id})}
status.textContent='Snapshot '+stamp(feed.fetched_at)+' · '+saved.length+' validated-format favorite quotes · research only. Fighter status and model calibration NOT VERIFIED.';draw();
}catch(e){status.textContent='UNAVAILABLE — '+e.message+' · no parlay recommendations';draw()}finally{btn.disabled=false}}
btn.addEventListener('click',load);legs.addEventListener('change',draw);load();
})();