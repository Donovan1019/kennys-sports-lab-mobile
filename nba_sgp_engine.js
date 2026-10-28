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
 return 'RETROSPECTIVE FIXED-THRESHOLD WALK-FORWARD BRIER '+(brier/tests).toFixed(3)+' over '+tests+' held-out dates (current prop lines applied to past games; not point-in-time valid, not prospective validation)';
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
function autoSgpCards(game,rows,profiles){
 const panel=el('section');panel.style.cssText='border:2px solid #35b889;border-radius:12px;padding:12px;margin:12px 0;background:#0b2930';
 panel.append(el('h4','AUTO NBA SGP · pregame research combinations'));
 const now=Date.now(),tip=Date.parse(game.commence_time);
 const eligible=rows.filter(x=>x.market.startsWith('player_')&&x.player&&Number.isFinite(Number(x.point))&&Number.isFinite(Number(x.price))&&Number(x.price)!==0&&x.bookmaker&&Number.isFinite(Date.parse(x.updated_at))&&Date.parse(x.updated_at)<=now&&now-Date.parse(x.updated_at)<=90*60000&&now<tip&&Number.isFinite(tip)&&Number.isFinite(prob(Number(x.price)))&&prob(Number(x.price))>=.5&&prob(Number(x.price))<1&&profiles.some(p=>String(p.name||'').trim().toLowerCase()===String(x.player).trim().toLowerCase()&&Array.isArray(p.games)&&p.games.length>=8));
 const ranked=[...eligible].sort((a,b)=>prob(Number(b.price))-prob(Number(a.price)));
 const specs=[['Safer two-leg research',2],['Balanced three-leg research',3],['Four-core research',4]];
 if(!ranked.length){panel.append(el('p','No automatic SGP cards: fresh, matched player props unavailable. No fabricated legs.'));const help=el('a','Refresh NBA player-prop quotes (GitHub workflow)');help.href='https://github.com/Donovan1019/kennys-sports-lab-mobile/actions/workflows/refresh-nba-nhl-props.yml';help.target='_blank';help.rel='noopener noreferrer';help.style.cssText='display:inline-block;padding:10px;border:1px solid #35b889;border-radius:8px;color:#a5f4d0';panel.append(help);panel.append(el('p','Select Run workflow → nba → max_events. Each event uses paid API credits. Fresh quotes must be captured before tipoff; historical player stats do not substitute for odds.'));return panel}
 for(const [label,count] of specs){
  const selected=[],used=new Set(),usedMarkets=new Set();
  for(const x of ranked){
   const identity=String(x.player).trim().toLowerCase(),key=identity+'|'+x.market;
   if(used.has(identity)||usedMarkets.has(x.market)||selected.some(y=>String(y.player).trim().toLowerCase()===identity&&y.market===x.market))continue;
   selected.push(x);used.add(identity);usedMarkets.add(x.market);
   if(selected.length===count)break;
  }
  const card=el('div');card.style.cssText='border:1px solid #42677b;border-radius:10px;padding:10px;margin:10px 0';
  card.append(el('strong',label+' · '+(selected.length===count?'AUTO GENERATED':'INSUFFICIENT MARKETS')));
  if(selected.length!==count){card.append(el('p','Only '+selected.length+'/'+count+' distinct-player and distinct-market legs verified. No complete parlay displayed.'));panel.append(card);continue}
  for(const x of selected){const line=el('p',x.player+' · '+buckets[x.market]+' '+x.selection+' '+x.point+' · '+x.bookmaker+' '+(Number(x.price)>0?'+':'')+x.price);line.style.cssText='margin:7px 0;padding:6px;border-bottom:1px solid #315163';card.append(line)}
  card.append(el('p','ORDERING: sportsbook implied probability only, not model confidence. SGP bookmaker price UNAVAILABLE · joint probability UNAVAILABLE · Monte Carlo validation UNAVAILABLE · fair odds/EV UNAVAILABLE · injury and lineup verification UNAVAILABLE · NOT BET ELIGIBLE.'));
  const copy=el('button','Copy research legs');copy.type='button';copy.addEventListener('click',()=>{const content=game.event+' · '+kickoff(game)+'\\n'+selected.map(x=>x.player+' '+buckets[x.market]+' '+x.selection+' '+x.point+' ('+x.bookmaker+' '+x.price+')').join('\\n')+'\\nRESEARCH ONLY — NOT BET ELIGIBLE; no SGP price or EV';if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(content).catch(()=>{copy.textContent='Clipboard unavailable'})});card.append(copy);panel.append(card);
 }
 panel.append(el('p','Automatic research cards are refreshed when the page loads or becomes visible. They are not sportsbook-verified parlays; stale or missing markets fail closed.'));
 return panel;
}
function renderGame(game,rows,playerProfiles){
 const section=el('article');section.style.cssText='border:1px solid #42677b;border-radius:12px;padding:14px;margin:14px 0;background:#10283a';
 const title=el('h3',game.event+' · '+kickoff(game));section.append(title);
 const intro=el('p','SGP research · sportsbook prices only. Correlation-adjusted simulations, verified player availability, fair odds and positive EV are REQUIRED before any bet is eligible.');section.append(intro);section.append(autoSgpCards(game,rows,playerProfiles));
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
const profiles=el('div');profiles.style.cssText='margin-top:12px;padding:10px;border:1px solid #42677b;border-radius:8px';profiles.append(el('h4','Player usage & historical minutes audit'));const matched=playerProfiles.filter(p=>[game.event.split(' @ ')[0],game.event.split(' @ ')[1]].some(t=>teamMatches(p.team,t)));profiles.append(el('p',matched.length+' historical player profiles matched to this matchup · current availability UNVERIFIED · projected minutes UNAVAILABLE.'));profiles.append(el('p','Historical recency gate: at least 8 dated player games, latest within 21 days. This does not verify current roster, injury or rotation status.'));for(const p of matched.slice(0,12)){const games=Array.isArray(p.games)?p.games:[];const minutes=games.map(g=>{const v=g.values||{};const k=Object.keys(v).find(k=>/^(minutes|min|mp)$/i.test(k.replace(/[^a-z]/gi,'')));return k?Number(v[k]):NaN}).filter(Number.isFinite).slice(0,10);const avg=minutes.length?minutes.reduce((a,b)=>a+b,0)/minutes.length:null;profiles.append(el('p',String(p.name||'Player')+' · '+p.team+' · '+games.length+' logged games · historical minutes L10: '+(avg===null?'UNAVAILABLE':avg.toFixed(1))+' ('+minutes.length+' samples) · injury/rotation UNVERIFIED'))}section.append(profiles);return section;
}
const teamMatches=(a,b)=>{const x=String(a||'').toLowerCase(),y=String(b||'').toLowerCase();return x.length>3&&(x===y||y.endsWith(' '+x)||x.endsWith(' '+y))};
async function load(){
 status.textContent='Loading NBA games and available sportsbook markets…';
 try{const response=await fetch('./feed/basketball_nba.json?sgp='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error('NBA feed HTTP '+response.status);
 const data=await response.json(),rows=Array.isArray(data.odds)?data.odds:[],now=Date.now(),events=new Map();
 let propRows=[];let propFeedStatus='player props feed unavailable';let propFeedFetchedAt=null;
 try{const propResponse=await fetch('./feed/nba_props.json?sgp='+Date.now(),{cache:'no-store'});if(propResponse.ok){const propData=await propResponse.json();propFeedFetchedAt=propData.fetched_at||null;const all=Array.isArray(propData.odds)?propData.odds:[];const feedAge=Date.parse(propFeedFetchedAt);const feedFresh=Number.isFinite(feedAge)&&feedAge<=now&&now-feedAge<=90*60000;propRows=feedFresh?all.filter(x=>x.event_id&&x.player&&x.market&&x.bookmaker&&Number.isFinite(Number(x.price))&&Number.isFinite(Date.parse(x.updated_at))&&Date.parse(x.updated_at)<=now&&now-Date.parse(x.updated_at)<=90*60000&&Number.isFinite(Date.parse(x.commence_time))&&Date.parse(x.commence_time)>now):[];propFeedStatus=propRows.length+' upcoming player prop rows';if(!propRows.length)propFeedStatus='no upcoming player prop rows (saved feed may be stale)'}}catch(_){/* no fabricated prop data */}
 rows.push(...propRows);let playerProfiles=[];try{const stats=await fetch('./feed/nba_player_stats.json',{cache:'no-store'});if(stats.ok){const history=await stats.json();playerProfiles=Array.isArray(history.players)?history.players:[]}}catch(_){/* history unavailable; no fabricated values */}
 for(const row of rows){if(!row.event_id||!row.event||!Number.isFinite(Date.parse(row.commence_time))||Date.parse(row.commence_time)<=now)continue;
 if(!events.has(row.event_id))events.set(row.event_id,{event_id:row.event_id,event:row.event,commence_time:row.commence_time,rows:[]});events.get(row.event_id).rows.push(row)}
 const games=[...events.values()].sort((a,b)=>Date.parse(a.commence_time)-Date.parse(b.commence_time));const today=etDate(now),todayGames=games.filter(g=>etDate(g.commence_time)===today),first=games[0]&&etDate(games[0].commence_time);
 const shown=todayGames.length?todayGames:games.filter(g=>etDate(g.commence_time)===first);
 output.replaceChildren();
 const propTime=Date.parse(propFeedFetchedAt);
 const propAge=Number.isFinite(propTime)?Math.round((now-propTime)/60000):null;
 const propHealth=propAge===null?'UNAVAILABLE':propAge<0?'INVALID FUTURE TIMESTAMP':propAge>90?'STALE — BLOCKED':'FRESH';
 const health=el('p','NBA SGP player-prop feed: '+propHealth+' · age '+(propAge===null?'unknown':propAge+' min')+' · accepted prop rows: '+propRows.length+' · 90-minute maximum · research only, not bet eligible.');
 health.setAttribute('role','status');
 health.style.cssText='border:1px solid #42677b;padding:10px;border-radius:8px;font-weight:600';
 output.append(health);
 const propEvents=new Set(propRows.map(x=>x.event_id));
 const covered=shown.filter(g=>propEvents.has(g.event_id)).length;
 const diagnostics=el('p','Player-prop coverage: '+covered+'/'+shown.length+' upcoming games · prop feed age '+(propAge===null?'unknown':propAge+' minutes')+' · refresh: GitHub Actions → Refresh NBA NHL Player Props (Credit-Limited) → Run workflow → nba. Paid API credits are used only on manual dispatch.');
 diagnostics.style.cssText='border:1px solid #42677b;padding:10px;border-radius:8px';
 output.append(diagnostics);const refresh=el('a','Open NBA player-prop refresh workflow');refresh.href='https://github.com/Donovan1019/kennys-sports-lab-mobile/actions/workflows/refresh-nba-nhl-props.yml';refresh.target='_blank';refresh.rel='noopener noreferrer';refresh.style.cssText='display:inline-block;margin:6px 0 12px;padding:10px;border:1px solid #35b889;border-radius:8px;color:#a5f4d0';output.append(refresh);
 const archiveStatus=el('p','Automated SGP archive: checking saved model capture status…');
 archiveStatus.style.cssText='border:1px solid #42677b;padding:10px;border-radius:8px';
 output.append(archiveStatus);
 try{
  const r=await fetch('./feed/nba_sgp_model_capture_status.json?sgp='+Date.now(),{cache:'no-store'});
  if(r.ok){
   const audit=await r.json();
   const age=Date.parse(audit.checked_at);
   const recent=Number.isFinite(age)&&age<=now&&now-age<=36*3600000;
   archiveStatus.textContent='Automated SGP ledger · '+(recent?String(audit.status||'UNVERIFIED'):'STATUS STALE / UNVERIFIED')+' · captured in latest run: '+Number(audit.captured||0)+' · source recommendations: '+Number(audit.source_recommendations||0)+' · rejected: '+Number(audit.rejected_count||0)+' · historical player profiles (8+ games): '+Number(audit.historical_player_profiles||0)+' · model validation: '+String(audit.model_validation_status||'UNAVAILABLE')+' · '+(audit.capture_ready?'verified source archive ready':'verified source archive not ready')+' · blockers: '+(Array.isArray(audit.source_blockers)&&audit.source_blockers.length?audit.source_blockers.join('; '):'none reported')+' · '+(audit.source_present?'source present':'model recommendation source missing')+' · research only, not placed bets.';
  }else archiveStatus.textContent='Automated SGP ledger: no saved capture report yet · UNVERIFIED.';
 }catch(_){archiveStatus.textContent='Automated SGP ledger status unavailable · UNVERIFIED.'}
 status.textContent=shown.length?'AUTO NBA SGP · '+shown.length+' upcoming games · '+(todayGames.length?'today':'next available date')+' · '+rows.length+' source market rows · '+propFeedStatus+' · RESEARCH ONLY':'AUTO NBA SGP · No upcoming NBA games in published market feed. Automatic cards require upcoming games and fresh verified player props; refresh NBA game and player-prop feeds.';
 if(!shown.length){const empty=el('section');empty.style.cssText='border:2px solid #35b889;border-radius:12px;padding:14px;margin:12px 0';empty.append(el('h3','AUTO NBA SGP · waiting for verified upcoming markets'));empty.append(el('p','No eligible upcoming game rows. The automatic two-, three-, and four-leg research cards will populate when the published schedule and fresh player-prop quotes are available. No synthetic parlays or prices are shown.'));output.append(empty)}
 for(const game of shown)output.append(renderGame(game,game.rows,playerProfiles));
 }catch(err){status.textContent='NBA SGP FEED ERROR: '+err.message+' · NOT BET ELIGIBLE';output.replaceChildren()}
}
load();document.addEventListener('visibilitychange',()=>{if(!document.hidden)load()});
})();