/* NBA SGP Engine v1: conservative market-based research, never a verified betting recommendation. */
(()=>{'use strict';
const root=document.getElementById('ksl-nba-sgp-root');if(!root)return;
const status=document.getElementById('nba-sgp-status'),output=document.getElementById('nba-sgp-games');
const etDate=v=>{const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(v));const part=k=>parts.find(x=>x.type===k).value;return part('year')+'-'+part('month')+'-'+part('day')};
const prob=price=>price<0?(-price)/(-price+100):100/(price+100);
const american=p=>p>=.5?'-'+Math.round(100*p/(1-p)):'+'+Math.round(100*(1-p)/p);
const el=(tag,txt)=>{const e=document.createElement(tag);if(txt!==undefined)e.textContent=txt;return e};
const teamName=(row)=>String(row.selection||'');
const buckets={h2h:'Moneyline',spreads:'Spread',totals:'Game total',player_points:'Points',player_rebounds:'Rebounds',player_assists:'Assists',player_threes:'Threes'};
const availableMarkets=new Set(['h2h','spreads','totals','player_points','player_rebounds','player_assists','player_threes']);
const kickoff=g=>new Date(g.commence_time).toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})+' ET';
function renderGame(game,rows){
 const section=el('article');section.style.cssText='border:1px solid #42677b;border-radius:12px;padding:14px;margin:14px 0;background:#10283a';
 const title=el('h3',game.event+' · '+kickoff(game));section.append(title);
 const intro=el('p','SGP research · sportsbook prices only. Correlation-adjusted simulations, verified player availability, fair odds and positive EV are REQUIRED before any bet is eligible.');section.append(intro);
 const select=el('select');select.setAttribute('aria-label','SGP market category');select.style.cssText='max-width:100%;padding:9px;background:#081426;color:white;border:1px solid #42677b;border-radius:8px';
 for(const [key,label] of Object.entries(buckets)){const opt=el('option',label);opt.value=key;select.append(opt)}
 section.append(select);
 const list=el('div');section.append(list);
 const draw=()=>{list.replaceChildren();const filtered=rows.filter(x=>x.market===select.value&&Number.isFinite(Number(x.price))&&Number(x.price)!==0).sort((a,b)=>Math.abs(Number(a.point||0))-Math.abs(Number(b.point||0))).slice(0,16);
 if(!filtered.length){list.append(el('p','No verified current '+buckets[select.value]+' prices in this feed.'));return}
 for(const row of filtered){const line=el('p');line.style.cssText='border-bottom:1px solid #294a5c;padding:8px 0;margin:0';const price=Number(row.price);line.textContent=(row.player?row.player+' · ':'')+teamName(row)+(row.point!==null&&row.point!==undefined?' '+row.point:'')+' · '+(price>0?'+':'')+price+' · '+row.bookmaker+' · implied '+(100*prob(price)).toFixed(1)+'%';list.append(line)}
 };select.addEventListener('change',draw);draw();
 const builder=el('div');builder.style.cssText='margin-top:12px;padding:10px;border:1px solid #5b6877;border-radius:8px';
 builder.append(el('strong','Conservative SGP builder · NOT BET ELIGIBLE'));
 builder.append(el('p','Four-core NBA framework: primary scorer points, lead rebounder rebounds, primary creator assists, and team/game scoring. Requires confirmed minutes, injuries, opponent matchups, pace and role before thresholds are selected.'));
 const markets=[...new Set(rows.map(x=>x.market))].filter(x=>availableMarkets.has(x));
 builder.append(el('p','Available source markets: '+(markets.map(x=>buckets[x]).join(', ')||'none')+'. Player prop markets absent from the source are explicitly unavailable.'));
 builder.append(el('p','Joint probability: UNAVAILABLE · correlation matrix: UNAVAILABLE · Monte Carlo: UNAVAILABLE · SGP price: UNAVAILABLE · fair odds: UNAVAILABLE · EV: UNAVAILABLE. Do not multiply independent leg probabilities or label this a recommended parlay.'));
 section.append(builder);return section;
}
async function load(){
 status.textContent='Loading NBA games and available sportsbook markets…';
 try{const response=await fetch('./feed/basketball_nba.json?sgp='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error('NBA feed HTTP '+response.status);
 const data=await response.json(),rows=Array.isArray(data.odds)?data.odds:[],now=Date.now(),events=new Map();
 for(const row of rows){if(!row.event_id||!row.event||!Number.isFinite(Date.parse(row.commence_time))||Date.parse(row.commence_time)<=now)continue;
 if(!events.has(row.event_id))events.set(row.event_id,{event_id:row.event_id,event:row.event,commence_time:row.commence_time,rows:[]});events.get(row.event_id).rows.push(row)}
 const games=[...events.values()].sort((a,b)=>Date.parse(a.commence_time)-Date.parse(b.commence_time));const today=etDate(now),todayGames=games.filter(g=>etDate(g.commence_time)===today),first=games[0]&&etDate(games[0].commence_time);
 const shown=todayGames.length?todayGames:games.filter(g=>etDate(g.commence_time)===first);
 output.replaceChildren();status.textContent=shown.length?'NBA SGP · '+shown.length+' upcoming games · '+(todayGames.length?'today':'next available date')+' · '+rows.length+' source market rows · RESEARCH ONLY':'No upcoming NBA games in published market feed. SGP unavailable until the next feed refresh.';
 for(const game of shown)output.append(renderGame(game,game.rows));
 }catch(err){status.textContent='NBA SGP FEED ERROR: '+err.message+' · NOT BET ELIGIBLE';output.replaceChildren()}
}
load();document.addEventListener('visibilitychange',()=>{if(!document.hidden)load()});
})();