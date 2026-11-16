/* 20 Club: verified 20+ point screen; no fabricated picks. */
(()=>{'use strict';const root=document.getElementById('ksl-20-club');if(!root)return;
const css=document.createElement('style');css.textContent='#ksl-20-club .club-card{background:#191a1d;border:1px solid #35383e;border-radius:12px;padding:12px;margin:9px 0}#ksl-20-club .club-metrics{display:flex;flex-wrap:wrap;gap:12px;color:#d1d9df;font-size:12px}#ksl-20-club strong{color:#f3c621}#ksl-20-club .club-green{color:#36c985}#ksl-20-club button{background:#173a35;color:#fff;border:1px solid #36c985;border-radius:8px;padding:9px}';document.head.append(css);
root.innerHTML='<h2>🏀 20 Club · Daily 20+ Points</h2><p>Current-season scoring trends, 20,000-draw historical Monte Carlo, verified 19.5-point quotes, and a near-even-money parlay target (-111 to +100). Historical simulations are not injury-adjusted forecasts.</p><p id="club-status" role="status">Loading current NBA feeds…</p><div id="club-parlay"></div><div id="club-cards"></div>';
const status=root.querySelector('#club-status'),cards=root.querySelector('#club-cards'),parlay=root.querySelector('#club-parlay');
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const oddsProb=o=>o<0?-o/(100-o):100/(100+o);
const decimal=o=>o<0?1+100/-o:1+o/100;
const american=d=>d>=2?'+'+Math.round(100*(d-1)):String(Math.round(-100/(d-1)));
const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
const pts=g=>{const v=g.values||{};const k=Object.keys(v).find(k=>['pts','points'].includes(norm(k)));const n=k==null?NaN:Number(v[k]);return Number.isFinite(n)&&n>=0?n:null};
const feed=async name=>{const r=await fetch('./feed/'+name+'?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(name+' HTTP '+r.status);return r.json()};
function simulate(hist,seed){let s=seed>>>0,hits=0;const out=[];for(let i=0;i<20000;i++){s=(Math.imul(1664525,s)+1013904223)>>>0;const v=hist[Math.floor((s/4294967296)*hist.length)];out.push(v);if(v>=20)hits++}out.sort((a,b)=>a-b);return {prob:hits/20000,low:out[1999],high:out[17999]}}
function add(parent,tag,text,cls){const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;parent.append(e);return e}
async function run(){try{const [stats,props]=await Promise.all([feed('nba_player_stats.json'),feed('nba_props.json')]);if(!Array.isArray(stats.players)||!Array.isArray(props.odds))throw Error('NBA player-statistics or props feed missing required players/odds arrays');if(!stats.players.length)throw Error('NBA player-statistics feed contains zero players; rebuild the player-log feed before publishing picks');
const now=Date.now(),quotes=new Map();for(const q of props.odds){const market=norm(q.market),selection=norm(q.selection||q.outcome||q.name),point=Number(q.point),price=Number(q.price),t=Date.parse(q.updated_at),tip=Date.parse(q.commence_time);
if(!['playerpoints','playerpointsalternate','playerpointsalts'].includes(market)||selection!=='over'||point!==19.5||!Number.isFinite(price)||price===0||price===-100||!['draftkings','fanduel'].includes(norm(q.bookmaker))||!Number.isFinite(t)||now-t>3600000||t>now||!Number.isFinite(tip)||tip<=now||!q.event_id)continue;
const name=norm(q.player||q.player_name||q.description),key=name+'|'+q.event_id+'|'+norm(q.bookmaker),old=quotes.get(key);if(name&&(!old||Date.parse(q.updated_at)>Date.parse(old.updated_at)))quotes.set(key,q)}
const rows=[];for(const p of stats.players){const logs=(p.games||[]).filter(g=>{const d=Date.parse(g.date);return Number.isFinite(d)&&d>=Date.parse('2026-10-01')&&d<now}).sort((a,b)=>Date.parse(b.date)-Date.parse(a.date)).map(pts).filter(v=>v!==null).slice(0,20);if(logs.length<10)continue;
for(const q of quotes.values()){if(norm(p.name)!==norm(q.player||q.player_name||q.description))continue;
const seed=[...norm(p.name)].reduce((s,c)=>(Math.imul(s,31)+c.charCodeAt(0))>>>0,12345),sim=simulate(logs,seed),l5=logs.slice(0,5),l10=logs.slice(0,10);
const proj=.5*mean(l5)+.3*mean(l10)+.2*mean(logs),breakEven=oddsProb(Number(q.price)),edge=sim.prob-breakEven;
rows.push({p,q,sim,proj,edge,breakEven,l5:l5.filter(x=>x>=20).length,l10:l10.filter(x=>x>=20).length,l20:logs.filter(x=>x>=20).length,n:logs.length,eligible:proj>=23&&sim.prob>=.75&&edge>=.025})}}
rows.sort((a,b)=>Number(b.eligible)-Number(a.eligible)||b.sim.prob-a.sim.prob);
status.textContent=rows.length+' matched fresh current-game 19.5 lines · '+rows.filter(r=>r.eligible).length+' screen candidates · Monte Carlo: 20,000 historical draws per player · No injury/minutes adjustment';
cards.replaceChildren();parlay.replaceChildren();if(!rows.length){const last=props.fetched_at||'unknown';add(cards,'p','UNAVAILABLE — No matching current-season logs and fresh 19.5-point sportsbook quotes. Latest props snapshot: '+last+'. Check NBA feed pipelines. No invented picks.');return}
for(const r of rows.slice(0,20)){const c=add(cards,'article','', 'club-card');add(c,'h3',r.p.name+' · '+(r.p.team||'NBA')+' · 20+ points');add(c,'p',r.q.bookmaker.toUpperCase()+' · Over 19.5 '+(Number(r.q.price)>0?'+':'')+r.q.price+' · '+(r.eligible?'HISTORICAL CANDIDATE':'PASS'));add(c,'div','L5 '+r.l5+'/5 · L10 '+r.l10+'/10 · L20 '+r.l20+'/'+r.n+' · Projected proxy '+r.proj.toFixed(1)+' · MC '+(r.sim.prob*100).toFixed(1)+'% · 80% range '+r.sim.low+'–'+r.sim.high+' · Proxy edge '+(r.edge*100).toFixed(1)+'pp','club-metrics')}
let best=null;const eligible=rows.filter(r=>r.eligible).slice(0,32);
const byBook=new Map();for(const r of eligible){const book=norm(r.q.bookmaker);if(!byBook.has(book))byBook.set(book,[]);byBook.get(book).push(r)}
// Bounded beam search avoids O(n^8) combinations while exploring 2–8 legs.
for(const group of byBook.values()){
let beam=[{picks:[],d:1,joint:1,usedPlayers:new Set(),usedGames:new Set()}];
for(let depth=1;depth<=8;depth++){
const next=[];for(const state of beam){const last=state.picks.length?group.indexOf(state.picks[state.picks.length-1]):-1;
for(let idx=last+1;idx<group.length;idx++){const r=group[idx],player=norm(r.p.name),game=String(r.q.event_id);
if(state.usedPlayers.has(player)||state.usedGames.has(game))continue;
const d=state.d*decimal(Number(r.q.price));if(!Number.isFinite(d)||d>2.000001)continue;
const joint=state.joint*r.sim.prob,usedPlayers=new Set(state.usedPlayers),usedGames=new Set(state.usedGames);usedPlayers.add(player);usedGames.add(game);
const candidate={picks:[...state.picks,r],d,joint,usedPlayers,usedGames};
if(depth>=2&&d>=1.90){const ev=joint*d-1;if(!best||joint>best.joint||(joint===best.joint&&ev>best.ev))best={...candidate,ev}}
if(depth<8)next.push(candidate)
}}
next.sort((a,b)=>b.d-a.d||b.joint-a.joint);beam=next.slice(0,1200);if(!beam.length)break
}}
add(parlay,'h3','20 Club · Target parlay (near even money: -111 to +100)');if(!best){add(parlay,'p','PASS — No qualifying same-book, distinct-game 2–8 leg combination near even money (-111 to +100).');return}
const box=add(parlay,'div','', 'club-card');for(const r of best.picks)add(box,'p',r.p.name+' 20+ · '+r.q.bookmaker.toUpperCase()+' '+(Number(r.q.price)>0?'+':'')+r.q.price);
add(box,'p','Reference combined odds '+american(best.d)+' · Independence-only probability '+(best.joint*100).toFixed(1)+'% · Break-even '+(100/best.d).toFixed(1)+'%');
add(box,'p','RESEARCH ONLY — Historical resampling does not adjust for injuries, expected minutes, matchup or cross-game dependence. Not a calibrated or verified betting-ready recommendation.');
}catch(e){status.textContent='UNAVAILABLE — '+e.message;cards.replaceChildren();parlay.replaceChildren()}}
run();
})();