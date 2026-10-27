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
function walkForwardAudit(historical){
 // Historical dates are newest first; evaluate each date using strictly older outcomes.
 const ordered=[...historical.outcomes].reverse();const minimumTrain=8;
 if(ordered.length<minimumTrain+5)return 'WALK-FORWARD UNAVAILABLE (requires 13+ aligned dates)';
 let brier=0,baselineBrier=0,tests=0;const base=ordered.reduce((a,b)=>a+b,0)/ordered.length;
 for(let i=minimumTrain;i<ordered.length;i++){
  const train=ordered.slice(0,i),successes=train.reduce((a,b)=>a+b,0);
  const forecast=(successes+1)/(train.length+2);const actual=ordered[i];
  brier+=(forecast-actual)**2;baselineBrier+=(base-actual)**2;tests++;
 }
 return 'DESCRIPTIVE WALK-FORWARD BRIER '+(brier/tests).toFixed(3)+' over '+tests+' held-out dates (smoothed historical-rate baseline; not prospective validation)';
}
function jointBootstrap(historical,draws){
 // Resample paired same-date joint outcomes as whole rows; never multiply leg probabilities.
 // Seeded deterministic generator for reproducible UI output.
 let seed=2166136261>>>0;for(const v of historical.outcomes){seed=Math.imul(seed^v,16777619)>>>0}
 const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
 const n=historical.outcomes.length,samples=[];let aggregate=0;
 for(let i=0;i<draws;i++){let successes=0;for(let j=0;j<n;j++)successes+=historical.outcomes[Math.floor(rand()*n)];const p=successes/n;samples.push(p);aggregate+=p}
 samples.sort((a,b)=>a-b);return {draws,p:aggregate/draws,lower:samples[Math.floor(.025*(draws-1))],upper:samples[Math.floor(.975*(draws-1))]};
}
function historicalJoint(legs,profiles){
 const fields={player_points:['points','pts'],player_rebounds:['rebounds','reb'],player_assists:['assists','ast'],player_threes:['threes','threepointersmade','fg3m','3pm']};
 if(!legs.every(x=>x.player&&fields[x.market]&&Number.isFinite(Number(x.point))&&/over|under/i.test(String(x.selection))))return {available:false,reason:'player over/under props with numeric lines required'};
 const series=legs.map(leg=>{const p=profiles.find(x=>String(x.name||'').trim().toLowerCase()===String(leg.player).trim().toLowerCase());if(!p)return null;const games=new Map();for(const g of p.games||[]){const date=String(g.date||'').slice(0,10);if(!/^\\d{4}-\\d{2}-\\d{2}$/.test(date))continue;const vals=g.values||{};const key=Object.keys(vals).find(k=>fields[leg.market].includes(k.toLowerCase().replace(/[^a-z0-9]/g,'')));const value=key?Number(vals[key]):NaN;if(Number.isFinite(value)&&value>=0)games.set(date,value)}return games});
 if(series.some(x=>!x))return {available:false,reason:'missing player profile'};
 const dates=[...series[0].keys()].filter(d=>series.every(m=>m.has(d))).sort().reverse().slice(0,20);
 if(dates.length<8)return {available:false,reason:'fewer than 8 aligned historical dates'};
 const outcomes=dates.map(d=>Number(legs.every((leg,i)=>{const v=series[i].get(d),line=Number(leg.point);return /over/i.test(leg.selection)?v>line:v<line})));
 const hits=outcomes.reduce((a,b)=>a+b,0);return {available:true,hits,n:dates.length,outcomes};
}
function renderGame(game,rows,playerProfiles){
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
 const freshnessTimes=rows.map(x=>Date.parse(x.updated_at)).filter(Number.isFinite);
 const lastQuote=freshnessTimes.length?Math.max(...freshnessTimes):NaN;
 const sourceAudit=el('p',Number.isFinite(lastQuote)?'Latest source quote: '+new Date(lastQuote).toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})+' ET · quote age '+Math.round((Date.now()-lastQuote)/60000)+' min · freshness gate ≤90 min':'Quote timestamp unavailable · NOT BET ELIGIBLE');
 section.append(sourceAudit);
 const builder=el('div');builder.style.cssText='margin-top:12px;padding:10px;border:1px solid #5b6877;border-radius:8px';
 builder.append(el('strong','Conservative SGP builder · NOT BET ELIGIBLE'));
 builder.append(el('p','Four-core NBA framework: primary scorer points, lead rebounder rebounds, primary creator assists, and team/game scoring. Requires confirmed minutes, injuries, opponent matchups, pace and role before thresholds are selected.'));
 const markets=[...new Set(rows.map(x=>x.market))].filter(x=>availableMarkets.has(x));
 builder.append(el('p','Available source markets: '+(markets.map(x=>buckets[x]).join(', ')||'none')+'. Player prop markets absent from the source are explicitly unavailable.'));
 const builderTitle=el('h4','SGP candidate builder · market audit');builder.append(builderTitle);
 const legChoices=rows.filter(x=>availableMarkets.has(x.market)&&Number.isFinite(Number(x.price))&&Number(x.price)!==0);
 const chosen=[];const chooser=el('select');chooser.setAttribute('aria-label','Choose SGP leg');
 chooser.style.cssText='max-width:100%;padding:9px;background:#081426;color:white;border:1px solid #42677b;border-radius:8px';
 const placeholder=el('option','Select a market leg');placeholder.value='';chooser.append(placeholder);
 legChoices.forEach((x,i)=>{const option=el('option',(x.player?x.player+' · ':'')+buckets[x.market]+' · '+x.selection+(x.point!==null&&x.point!==undefined?' '+x.point:'')+' · '+(Number(x.price)>0?'+':'')+x.price+' ('+x.bookmaker+')');option.value=String(i);chooser.append(option)});
 builder.append(chooser);
 const add=el('button','Add leg');add.type='button';add.style.cssText='padding:9px;margin:8px;border-radius:8px;cursor:pointer';
 const clear=el('button','Clear');clear.type='button';clear.style.cssText='padding:9px;border-radius:8px;cursor:pointer';
 const selectedList=el('div');const result=el('p');
 function redraw(){selectedList.replaceChildren();for(const x of chosen)selectedList.append(el('p',(x.player?x.player+' · ':'')+buckets[x.market]+' · '+x.selection+(x.point!==null&&x.point!==undefined?' '+x.point:'')+' · '+x.bookmaker));
 result.textContent=chosen.length+' legs selected · '+[...new Set(chosen.map(x=>x.player||x.selection))].length+' unique selections · SGP joint probability UNAVAILABLE · correlated Monte Carlo UNAVAILABLE · bookmaker SGP quote UNAVAILABLE · EV UNAVAILABLE · NOT BET ELIGIBLE.'}
 add.addEventListener('click',()=>{const x=legChoices[Number(chooser.value)];if(chooser.value===''||!x||chosen.length>=6)return;
 if(chosen.some(y=>y===x))return;
 const marketKey=y=>[String(y.player||y.selection||'').trim().toLowerCase(),y.market,String(y.point)].join('|');
 const opposite=y=>String(y.selection||'').toLowerCase().includes('over')?'under':String(y.selection||'').toLowerCase().includes('under')?'over':'';
 if(chosen.some(y=>marketKey(y)===marketKey(x)&&opposite(y)!==opposite(x)))return;
 if(chosen.some(y=>marketKey(y)===marketKey(x)&&opposite(y)===opposite(x)))return;
 chosen.push(x);redraw()});clear.addEventListener('click',()=>{chosen.length=0;redraw()});
 builder.append(add,clear,selectedList,result);redraw();
 builder.append(el('p','Leg integrity: duplicate or opposite-side selections at the same player/market/line are rejected. All legs must belong to this game.'));
 builder.append(el('p','Preflight: leg eligibility, roster status, current minutes, same-game correlation, joint simulation, SGP-specific price and EV must all pass. This interface never estimates joint odds by multiplying independent probabilities.'));
 const simulation=el('div');simulation.style.cssText='border-top:1px solid #42677b;padding-top:12px;margin-top:12px';
 simulation.append(el('h4','Joint simulation research · gated'));
 const run=el('button','Run SGP simulation audit');run.type='button';run.style.cssText='padding:9px;border-radius:8px;cursor:pointer';
 const simulationResult=el('p','Simulation not run.');simulation.append(run,simulationResult);
 run.addEventListener('click',()=>{
  if(chosen.length<2){simulationResult.textContent='Select at least two legs. Simulation unavailable.';return}
  const missing=[];if(!chosen.every(x=>x.player&&availableMarkets.has(x.market)&&x.market.startsWith('player_')))missing.push('joint game/team scoring model');
  if(!chosen.every(x=>x.player&&playerProfiles.some(p=>String(p.name||'').trim().toLowerCase()===String(x.player||'').trim().toLowerCase())))missing.push('matched player game logs');
  const freshness=rows.filter(x=>x.updated_at).map(x=>Date.parse(x.updated_at)).filter(Number.isFinite);
  const newest=freshness.length?Math.max(...freshness):NaN;
  const age=Number.isFinite(newest)?Math.round((Date.now()-newest)/60000):null;
  const preflight=[];
  if(age===null||age<0||age>90)preflight.push('market quotes stale or timestamp unavailable ('+(age===null?'unknown':age+' minutes')+')');
  if(chosen.some(x=>!x.bookmaker||!Number.isFinite(Number(x.price))))preflight.push('missing book/price');
  if(chosen.some(x=>!x.player))preflight.push('team/game legs require separate game model');
  const playerAudit=chosen.filter(x=>x.player).map(x=>{const profile=playerProfiles.find(p=>String(p.name||'').trim().toLowerCase()===String(x.player||'').trim().toLowerCase());if(!profile)return x.player+': missing player history';const games=Array.isArray(profile.games)?profile.games:[];const dated=games.map(g=>Date.parse(g.date)).filter(Number.isFinite).sort((a,b)=>b-a);if(dated.length<8)return x.player+': fewer than 8 dated games';if(Date.now()-dated[0]>21*86400000)return x.player+': last logged game older than 21 days';return null}).filter(Boolean);
  if(playerAudit.length)preflight.push(...playerAudit);
  const historic=historicalJoint(chosen,playerProfiles);
  if(preflight.length){simulationResult.textContent='SOURCE / PLAYER QUALITY BLOCKED · '+preflight.join('; ')+' · simulation not run · NOT BET ELIGIBLE';return}
  if(historic.available){const mc=jointBootstrap(historic,10000);const audit=walkForwardAudit(historic);simulationResult.textContent='EXPERIMENTAL PAIRED-DATE BOOTSTRAP · '+mc.draws.toLocaleString()+' resamples · joint historical co-hit '+historic.hits+'/'+historic.n+' ('+(100*historic.hits/historic.n).toFixed(1)+'%) · resampled '+(100*mc.p).toFixed(1)+'% · bootstrap 95% interval '+(100*mc.lower).toFixed(1)+'–'+(100*mc.upper).toFixed(1)+'% · '+audit+' · same-date outcomes preserved, but this is NOT a calibrated forward-looking SGP probability · injuries/lineups UNVERIFIED · SGP quote and EV UNAVAILABLE · NOT BET ELIGIBLE.';return}
  missing.push('verified starting lineups and injuries','aligned same-game player outcomes ('+historic.reason+')','calibrated joint residual distribution','bookmaker SGP quote');
  simulationResult.textContent='BLOCKED · '+chosen.length+' legs · missing: '+[...new Set(missing)].join('; ')+'. Monte Carlo NOT RUN. Joint probability, fair odds and EV UNAVAILABLE. Do not treat individual implied probabilities as independent.';
 });builder.append(simulation);
 section.append(builder);const profiles=el('div');profiles.style.cssText='margin-top:12px;padding:10px;border:1px solid #42677b;border-radius:8px';profiles.append(el('h4','Player usage & historical minutes audit'));const matched=playerProfiles.filter(p=>[game.event.split(' @ ')[0],game.event.split(' @ ')[1]].some(t=>teamMatches(p.team,t)));profiles.append(el('p',matched.length+' historical player profiles matched to this matchup · current availability UNVERIFIED · projected minutes UNAVAILABLE.'));profiles.append(el('p','Historical recency gate: at least 8 dated player games, latest within 21 days. This does not verify current roster, injury or rotation status.'));for(const p of matched.slice(0,12)){const games=Array.isArray(p.games)?p.games:[];const minutes=games.map(g=>{const v=g.values||{};const k=Object.keys(v).find(k=>/^(minutes|min|mp)$/i.test(k.replace(/[^a-z]/gi,'')));return k?Number(v[k]):NaN}).filter(Number.isFinite).slice(0,10);const avg=minutes.length?minutes.reduce((a,b)=>a+b,0)/minutes.length:null;profiles.append(el('p',String(p.name||'Player')+' · '+p.team+' · '+games.length+' logged games · historical minutes L10: '+(avg===null?'UNAVAILABLE':avg.toFixed(1))+' ('+minutes.length+' samples) · injury/rotation UNVERIFIED'))}section.append(profiles);return section;
}
const teamMatches=(a,b)=>{const x=String(a||'').toLowerCase(),y=String(b||'').toLowerCase();return x.length>3&&(x===y||y.endsWith(' '+x)||x.endsWith(' '+y))};
async function load(){
 status.textContent='Loading NBA games and available sportsbook markets…';
 try{const response=await fetch('./feed/basketball_nba.json?sgp='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error('NBA feed HTTP '+response.status);
 const data=await response.json(),rows=Array.isArray(data.odds)?data.odds:[],now=Date.now(),events=new Map();
 let propRows=[];let propFeedStatus='player props feed unavailable';let propFeedFetchedAt=null;
 try{const propResponse=await fetch('./feed/nba_props.json?sgp='+Date.now(),{cache:'no-store'});if(propResponse.ok){const propData=await propResponse.json();propFeedFetchedAt=propData.fetched_at||null;const all=Array.isArray(propData.odds)?propData.odds:[];propRows=all.filter(x=>x.event_id&&x.player&&x.market&&Number.isFinite(Date.parse(x.commence_time))&&Date.parse(x.commence_time)>now);propFeedStatus=propRows.length+' upcoming player prop rows';if(!propRows.length)propFeedStatus='no upcoming player prop rows (saved feed may be stale)'}}catch(_){/* no fabricated prop data */}
 rows.push(...propRows);let playerProfiles=[];try{const stats=await fetch('./feed/nba_player_stats.json',{cache:'no-store'});if(stats.ok){const history=await stats.json();playerProfiles=Array.isArray(history.players)?history.players:[]}}catch(_){/* history unavailable; no fabricated values */}
 for(const row of rows){if(!row.event_id||!row.event||!Number.isFinite(Date.parse(row.commence_time))||Date.parse(row.commence_time)<=now)continue;
 if(!events.has(row.event_id))events.set(row.event_id,{event_id:row.event_id,event:row.event,commence_time:row.commence_time,rows:[]});events.get(row.event_id).rows.push(row)}
 const games=[...events.values()].sort((a,b)=>Date.parse(a.commence_time)-Date.parse(b.commence_time));const today=etDate(now),todayGames=games.filter(g=>etDate(g.commence_time)===today),first=games[0]&&etDate(games[0].commence_time);
 const shown=todayGames.length?todayGames:games.filter(g=>etDate(g.commence_time)===first);
 output.replaceChildren();
 const propAge=propFeedFetchedAt&&Number.isFinite(Date.parse(propFeedFetchedAt))?Math.round((now-Date.parse(propFeedFetchedAt))/60000):null;
 const propEvents=new Set(propRows.map(x=>x.event_id));
 const covered=shown.filter(g=>propEvents.has(g.event_id)).length;
 const diagnostics=el('p','Player-prop coverage: '+covered+'/'+shown.length+' upcoming games · prop feed age '+(propAge===null?'unknown':propAge+' minutes')+' · refresh: GitHub Actions → Refresh NBA NHL Player Props (Credit-Limited) → Run workflow → nba. Paid API credits are used only on manual dispatch.');
 diagnostics.style.cssText='border:1px solid #42677b;padding:10px;border-radius:8px';
 output.append(diagnostics);
 status.textContent=shown.length?'NBA SGP · '+shown.length+' upcoming games · '+(todayGames.length?'today':'next available date')+' · '+rows.length+' source market rows · '+propFeedStatus+' · RESEARCH ONLY':'No upcoming NBA games in published market feed. SGP unavailable until the next feed refresh.';
 for(const game of shown)output.append(renderGame(game,game.rows,playerProfiles));
 }catch(err){status.textContent='NBA SGP FEED ERROR: '+err.message+' · NOT BET ELIGIBLE';output.replaceChildren()}
}
load();document.addEventListener('visibilitychange',()=>{if(!document.hidden)load()});
})();