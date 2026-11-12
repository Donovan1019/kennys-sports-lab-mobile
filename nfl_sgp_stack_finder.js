(()=>{'use strict';
const root=document.getElementById('nfl-sgp-stack-finder');if(!root)return;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const windows=['Thursday Night','Sunday International / Morning','Sunday 1 PM','Sunday 4 PM','Sunday Night','Monday Night','Saturday / Special','Other'];
const et=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',weekday:'short',hour:'numeric',minute:'2-digit',hour12:false});
function windowOf(iso){const parts=Object.fromEntries(et.formatToParts(new Date(iso)).filter(p=>p.type!=='literal').map(p=>[p.type,p.value]));const day=parts.weekday,h=Number(parts.hour)%24;if(day==='Thu')return windows[0];if(day==='Mon')return windows[5];if(day==='Sat')return windows[6];if(day==='Sun'){if(h<12)return windows[1];if(h<15)return windows[2];if(h<19)return windows[3];return windows[4]}return windows[7]}
const formatTime=t=>new Date(t).toLocaleString('en-US',{timeZone:'America/New_York',weekday:'short',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'});
const label={player_pass_yds:'Pass yards',player_pass_tds:'Pass TDs',player_rush_yds:'Rush yards',player_reception_yds:'Receiving yards',player_receptions:'Receptions',player_anytime_td:'Anytime TD'};
const price=p=>p>0?'+'+p:String(p);

const SGP_TIERS=Object.freeze([{id:'gold',name:'Gold',snap:.70,routes:.75,targets:6,odds:'+100 to +200'},{id:'silver',name:'Silver',snap:.65,routes:.70,targets:5,odds:'+200 to +400'},{id:'bronze',name:'Bronze',snap:.55,routes:.60,targets:4,odds:'+400 to +800'}]);
const SGP_MARKET_GROUPS=Object.freeze({
 game:['h2h','spreads','totals','alternate_spreads','alternate_totals'],
 team:['team_totals','alternate_team_totals','team_to_score_first','team_to_score_last'],
 passing:['player_pass_yds','player_pass_tds','player_pass_attempts','player_pass_completions','player_pass_interceptions','player_pass_longest_completion'],
 rushing:['player_rush_yds','player_rush_attempts','player_rush_longest'],
 receiving:['player_reception_yds','player_receptions','player_targets','player_reception_longest'],
 scoring:['player_anytime_td','player_1st_td','player_2_plus_tds','player_field_goals','player_kicking_points','player_extra_points','player_field_goals_made'],
 defense:['player_sacks','player_tackles_assists','player_interceptions']
});
const SGP_MARKET_IDS=new Set(Object.values(SGP_MARKET_GROUPS).flat());
function sgpLegCountValid(legs){return Array.isArray(legs)&&legs.length>=1&&legs.length<=5}
function sgpSameGame(legs){return sgpLegCountValid(legs)&&legs.every(x=>x&&x.event_id&&x.event_id===legs[0].event_id)}
function sgpNoConflictingSelections(legs){const seen=new Map();for(const x of legs){if(!x||!SGP_MARKET_IDS.has(x.market))return false;const key=[x.bookmaker,x.event_id,x.player||x.team||'',x.market,Number(x.point)].join('|');if(seen.has(key)&&seen.get(key)!==x.selection)return false;seen.set(key,x.selection)}return true}
window.KSLNFL_SGP_MARKET_GROUPS=SGP_MARKET_GROUPS;
window.KSLNFL_SGP_VALIDATE_LEGS=legs=>sgpSameGame(legs)&&sgpNoConflictingSelections(legs);
function sgpUsageEligible(leg,u,t){if(!leg||!leg.player||!leg.event_id||!u||!u.event_id||u.verified!==true||u.player!==leg.player||u.event_id!==leg.event_id||u.injury_verified!==true||u.role_stable!==true||!Number.isFinite(u.snap_share)||u.snap_share<t.snap)return false;if(['player_receptions','player_reception_yds'].includes(leg.market)&&leg.selection==='Over'&&(!Number.isFinite(u.route_participation)||u.route_participation<t.routes||!Number.isFinite(u.projected_targets)||u.projected_targets<t.targets))return false;if(leg.market==='player_rush_yds'&&leg.selection==='Over'&&(!Number.isFinite(u.projected_carries)||u.projected_carries<8))return false;if(leg.selection==='Under'&&u.under_role_verified!==true)return false;return true}
function readinessDiagnostics(odds,readiness,calibration){
 const rows=Array.isArray(odds?.odds)?odds.odds:[];
 const times=rows.map(q=>Date.parse(q.updated_at)).filter(Number.isFinite);
 const newest=times.length?Math.max(...times):NaN;
 const quotesFresh=Number.isFinite(newest)&&Date.now()-newest<=30*60000&&Date.now()>=newest;
 const forecastReady=Number(readiness?.sports?.NFL?.fully_verified_player_recommendations)>0;
 const calibrated=calibration?.bet_eligibility==='ELIGIBLE';
 const reasons=[];
 if(!rows.length)reasons.push('No NFL player prop quotes available');
 if(!quotesFresh)reasons.push('Fresh DK/FD quote timestamps unavailable (30-minute maximum)');
 if(!forecastReady)reasons.push('No fully verified NFL player forecasts');
 if(!calibrated)reasons.push('Joint forecast calibration is not approved');
 reasons.push('Independent player usage / injury / role verification and official combined SGP prices are not connected');
 return '<details style="border:1px solid #47617a;border-radius:10px;padding:12px;margin:10px 0"><summary><strong>SGP readiness audit · '+(reasons.length?'BLOCKED':'READY')+'</strong></summary><ul>'+reasons.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul><p style="font-size:12px">Refreshing this page reads published data only. To update the source, run the NFL prop workflow. Missing verification must not be replaced with historical hit rates or estimated prices.</p></details>';
}
function sgpMarketCoverage(game){
 const offered=new Set(game.rows.map(x=>x.market).filter(x=>SGP_MARKET_IDS.has(x)));
 const groups=Object.entries(SGP_MARKET_GROUPS).map(([name,markets])=>({name,offered:markets.filter(m=>offered.has(m))}));
 const total=groups.reduce((n,g)=>n+g.offered.length,0);
 return '<details style="margin:8px 0"><summary>Available game markets: '+total+' of '+SGP_MARKET_IDS.size+' recognized</summary><p style="font-size:12px">These are markets observed in the published feed, not verified betting recommendations. One leg is a single bet; two to five legs form an SGP.</p><ul>'+groups.map(g=>'<li>'+esc(g.name)+': '+(g.offered.length?g.offered.map(esc).join(', '):'not in current feed')+'</li>').join('')+'</ul></details>';
}
function existingGameSimulation(game){
 const api=window.KSL_NFL_ML_ENGINE;
 if(!api||typeof api.getGames!=='function'||typeof api.simulation!=='function')return '<p style="font-size:12px">Existing NFL game simulator not loaded on this page.</p>';
 const normTeam=x=>String(x||'').toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g,' ').trim();
 const nameParts=String(game.name||'').split(/\s+@\s+/);
 const matches=api.getGames().filter(g=>{
  if(g.event_id===game.event_id)return true;
  if(nameParts.length!==2||!g.away||!g.home)return false;
  const a=Date.parse(g.commence_time),b=Date.parse(game.time);
  return Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=15*60000&&normTeam(g.away)===normTeam(nameParts[0])&&normTeam(g.home)===normTeam(nameParts[1]);
 });
 if(matches.length!==1)return '<p style="font-size:12px">No unique verified matchup-and-kickoff match in the existing NFL game simulator. No model probability inferred.</p>';
 const sim=api.simulation(matches[0]);
 if(!sim||!Number.isFinite(sim.n)||sim.n<=0||!Number.isFinite(sim.aWins)||!Number.isFinite(sim.hWins))return '<p style="font-size:12px">Existing historical scoring simulator lacks sufficient team history.</p>';
 const away=100*sim.aWins/sim.n,home=100*sim.hWins/sim.n,tie=100*(sim.ties||0)/sim.n;
 return '<details style="margin:8px 0"><summary>Existing NFL game simulation · RESEARCH ONLY</summary><p style="font-size:12px">'+esc(matches[0].away)+' win '+away.toFixed(1)+'% · '+esc(matches[0].home)+' win '+home.toFixed(1)+'% · simulated ties '+tie.toFixed(1)+'% · '+sim.n+' historical scoring draws.</p><small>Uncalibrated historical scoring model; not a same-game correlated player-prop simulator, sportsbook price, or bet recommendation.</small></details>';
}
function calibrationAudit(calibration){
 const markets=calibration?.frozen_forward_holdout?.markets||{};
 const entries=Object.entries(markets);
 if(!entries.length)return '<p style="font-size:12px">No verified NFL player-prop calibration report loaded; player-prop recommendations blocked.</p>';
 const approved=entries.filter(([,v])=>v?.eligible_for_live_use===true).length;
 const metric=x=>Number.isFinite(Number(x))?Number(x).toFixed(4):'UNAVAILABLE';return '<details style="margin:8px 0"><summary>Player-prop calibration audit · '+approved+'/'+entries.length+' approved</summary><ul>'+entries.map(([market,v])=>'<li>'+esc(market)+': '+esc(v?.status||'UNVERIFIED')+' · live use '+(v?.eligible_for_live_use===true?'ELIGIBLE':'BLOCKED')+' · holdout n='+esc(v?.holdout_samples??'unknown')+' · Brier '+metric(v?.raw_brier)+' → '+metric(v?.frozen_brier)+' · ECE '+metric(v?.raw_ece)+' → '+metric(v?.frozen_ece)+'</li>').join('')+'</ul><small>'+esc(calibration?.method||'Method unavailable')+'. '+esc(calibration?.acceptance_gate_policy||'No approval policy supplied')+' Approval does not establish player availability, same-game correlation, or official SGP pricing.</small></details>';
}
function noCreditSimulatedCandidates(game){
 const engine=window.KSL_NFL_ML_ENGINE;
 if(!engine||typeof engine.getGames!=='function'||typeof engine.simulation!=='function')return '<p>Game-model SGP candidates awaiting existing scoring simulation.</p>';
 const match=(engine.getGames()||[]).find(g=>norm(g.event)===norm(game.name)&&Math.abs(Date.parse(g.commence_time)-Date.parse(game.time))<=900000);
 if(!match)return '<p>Game-model SGP candidates unavailable: no exact scheduled matchup in scoring feed.</p>';
 const sim=engine.simulation(match);
 if(!sim||!Array.isArray(sim.draws)||sim.draws.length<1000)return '<p>Game-model SGP candidates unavailable: insufficient scoring history.</p>';
 const half=x=>Math.round(Number(x))+0.5;
 const totalLine=half(sim.total.mid),awayLine=half(sim.away.mid),homeLine=half(sim.home.mid);
 const defs=[
  {name:'Home scoring stack',legs:[{label:match.home+' ML',test:d=>d.home>d.away},{label:match.home+' team total OVER '+homeLine+' (model threshold)',test:d=>d.home>homeLine}]},
  {name:'Away scoring stack',legs:[{label:match.away+' ML',test:d=>d.away>d.home},{label:match.away+' team total OVER '+awayLine+' (model threshold)',test:d=>d.away>awayLine}]},
  {name:'Defensive game stack',legs:[{label:'Game total UNDER '+totalLine+' (model threshold)',test:d=>d.total<totalLine},{label:match.home+' team total UNDER '+homeLine+' (model threshold)',test:d=>d.home<homeLine}]}
 ];
 const cards=defs.map(x=>{
  const n=sim.draws.filter(d=>x.legs.every(l=>l.test(d))).length;
  const p=n/sim.draws.length;
  return '<article style="border:1px solid #47617a;border-radius:8px;padding:10px;margin:9px 0"><strong>'+esc(x.name)+'</strong><ol>'+x.legs.map(l=>'<li>'+esc(l.label)+'</li>').join('')+'</ol><p>Joint historical-scoring simulation: '+(p*100).toFixed(1)+'% ('+n+'/'+sim.draws.length+' draws) · RESEARCH ONLY</p><small>Thresholds are model-derived, NOT available sportsbook lines. Odds, EV, current roster/injury status and calibration unavailable. Not betting eligible.</small></article>';
 }).join('');
 return '<section style="border:1px solid #4a708d;border-radius:10px;padding:12px;margin:12px 0"><h4>Simulated SGP candidates · no-credit mode</h4><p>Actual two-leg game-market selections from the existing 10,000-draw historical scoring simulator. No player props are implied. Joint frequencies are not validated win probabilities.</p>'+cards+'</section>';
}
function noCreditPlayerProps(game){
 const rows=Array.isArray(game.rows)?game.rows:[];
 const byPlayer=new Map();
 for(const x of rows){
  if(!x.player||!x.market||!Number.isFinite(Number(x.point))||!['Over','Under'].includes(x.selection))continue;
  const key=String(x.player)+'|'+String(x.market)+'|'+String(x.point);
  if(!byPlayer.has(key))byPlayer.set(key,[]);
  byPlayer.get(key).push(x);
 }
 const eligible=[...byPlayer].filter(([key,v])=>v.some(x=>x.selection==='Over')&&v.some(x=>x.selection==='Under'));
 if(!eligible.length)return '<section style="border:1px solid #47617a;border-radius:10px;padding:12px;margin:10px 0"><strong>Player SGP candidates unavailable</strong><p>No verified named-player, two-sided prop markets and thresholds are published for this matchup. The model will not substitute unnamed QB/WR placeholders or invented player lines.</p><p>Historical game-market simulations, where available, are separate research and are not player-prop parlays.</p></section>';
 return '<section><strong>Named player markets available for independent verification</strong><ul>'+eligible.slice(0,12).map(([key])=>'<li>'+esc(key.split('|').join(' · '))+'</li>').join('')+'</ul><p>Market coverage only. Not a parlay recommendation without independent player forecast, verified status and joint simulation.</p></section>';
}
function tierPanel(game, paired=[], researchLegs=[], researchJoint=null){
 const cards=SGP_TIERS.map((t,i)=>{
  const count=i+2;
  const research=researchLegs.filter(x=>x&&x.player&&Number.isFinite(Number(x.point)));
  const source=research.length>=count?research:paired.map(p=>p.Over).filter(q=>q&&q.player&&Number.isFinite(Number(q.point))).map(q=>({player:q.player,market:q.market,point:q.point,selection:'Over',bookmaker:q.bookmaker}));
  const unique=[];const seen=new Set();let book=null;
  for(const leg of source){const q=game.rows.find(x=>x.player===leg.player&&x.market===leg.market&&Number(x.point)===Number(leg.point)&&x.selection===leg.selection&&(!leg.bookmaker||x.bookmaker===leg.bookmaker)&&(!book||x.bookmaker===book));if(!q||seen.has(q.player))continue;if(!book)book=q.bookmaker;seen.add(q.player);unique.push(q);if(unique.length===count)break}
  const valid=unique.length===count;
  const isHistorical=research.length>=count;
  const list=valid?'<ol style="padding-left:22px">'+unique.map(q=>'<li>'+esc(q.player)+' · '+esc(label[q.market]||q.market)+' '+esc(q.selection)+' '+esc(q.point)+' · '+esc(price(q.price))+'</li>').join('')+'</ol>':'<p>Insufficient same-book two-way player markets for '+count+' distinct players.</p>';
  return '<div style="border:1px solid #47617a;border-radius:8px;padding:10px;margin:7px 0"><strong>'+esc(t.name)+' SGP</strong> · target '+esc(t.odds)+'<p style="font-size:12px;margin:5px 0"><strong>RESEARCH EXAMPLE — NOT BET ELIGIBLE</strong> · '+(valid?esc(book)+' · '+count+' quoted legs':'No complete example')+'</p>'+list+'<small>'+(isHistorical?'Historical direction research only; not a forward-calibrated SGP forecast. ':'Illustrative Over-side market combination, NOT a model pick. ')+'Individual quotes are not an executable combined SGP price; target odds are not verified. Player availability and joint correlation unverified. '+(researchJoint?.status==='EXPERIMENTAL'?'Historical bootstrap is experimental, not a betting probability.':'No qualified joint simulation.')+'</small></div>';
 }).join('');
 return '<section aria-label="Gold Silver Bronze SGP tiers for '+esc(game.name)+'" style="margin:8px 0"><strong>Gold · Silver · Bronze · research examples</strong>'+cards+sgpMarketCoverage(game)+'</section>'
}
window.KSLNFL_SGP_TIERS=SGP_TIERS;window.KSLNFL_SGP_USAGE_ELIGIBLE=sgpUsageEligible;
const riskFor=market=>({player_pass_yds:'Passing volume / blowout',player_pass_tds:'Red-zone conversion / low scoring',player_rush_yds:'Run-pass split / trailing script',player_reception_yds:'Target share / yards per catch',player_receptions:'Routes / target share',player_anytime_td:'Touchdown variance / goal-line usage'})[market]||'Role uncertainty';
function scriptAudit(legs){const counts={pass:0,rush:0,receive:0,td:0};for(const x of legs){if(x.market==='player_pass_yds'||x.market==='player_pass_tds')counts.pass++;if(x.market==='player_rush_yds')counts.rush++;if(x.market==='player_receptions'||x.market==='player_reception_yds')counts.receive++;if(x.market==='player_anytime_td'||x.market==='player_pass_tds')counts.td++}const flags=[];if(counts.pass&&counts.receive)flags.push('Shared passing-volume exposure: QB and receiver legs may fail together');if(counts.pass&&counts.rush)flags.push('Run/pass game-script conflict: test leading and trailing scripts');if(counts.td)flags.push('TD conversion volatility: do not infer TD probability from yardage');if(legs.some(x=>x.market==='player_rush_yds')&&legs.some(x=>x.market==='player_receptions'||x.market==='player_reception_yds'))flags.push('RB usage split: rushing and receiving opportunities need separate forecasts');if(!flags.length)flags.push('Player usage, injury status, and shared game script still require validation');return flags}
let lastRenderArgs=null;
window.addEventListener('ksl-nfl-moneyline-ready',()=>{if(lastRenderArgs)render(...lastRenderArgs)});
function render(d,stats,ledger,readiness,calibration){lastRenderArgs=[d,stats,ledger,readiness,calibration];const odds=(d.odds||[]).filter(x=>x.event_id&&x.commence_time&&x.player&&Number.isFinite(Number(x.price))&&['draftkings','fanduel'].includes(x.bookmaker)&&Number.isFinite(Date.parse(x.updated_at))&&Date.now()>=Date.parse(x.updated_at)&&new Date(x.commence_time)>new Date());
const games=new Map();for(const o of odds){if(!games.has(o.event_id))games.set(o.event_id,{event_id:o.event_id,name:o.event,time:o.commence_time,rows:[]});games.get(o.event_id).rows.push(o)}
const coreRows=(Array.isArray(d.core_odds)?d.core_odds:[]).filter(x=>x&&x.event_id&&x.commence_time&&['h2h','spreads','totals'].includes(x.market)&&typeof x.selection==='string'&&x.selection.trim()&&Number.isFinite(Number(x.price))&&Math.abs(Number(x.price))>=100&&['draftkings','fanduel'].includes(x.bookmaker)&&Number.isFinite(Date.parse(x.updated_at))&&Date.now()-Date.parse(x.updated_at)<=30*60000&&Date.now()>=Date.parse(x.updated_at)&&new Date(x.commence_time)>new Date());
const coreUnique=new Map();for(const o of coreRows){const key=[o.event_id,o.bookmaker,o.market,o.selection,o.point].join('|');const prev=coreUnique.get(key);if(!prev||Date.parse(o.updated_at)>Date.parse(prev.updated_at))coreUnique.set(key,o)}for(const o of coreUnique.values()){if(!games.has(o.event_id))games.set(o.event_id,{event_id:o.event_id,name:o.event||'NFL matchup',time:o.commence_time,rows:[]});games.get(o.event_id).rows.push(o)}
// Schedule is independent of sportsbook coverage. Keep upcoming games visible
// when event-level player props are unavailable or credit-limited.
const scheduleRows=Array.isArray(d.schedule_games)?d.schedule_games:[];
for(const g of scheduleRows){
 if(!g||!g.event_id||!g.commence_time||!Number.isFinite(Date.parse(g.commence_time))||Date.parse(g.commence_time)<=Date.now())continue;
 const already=[...games.values()].some(x=>Math.abs(Date.parse(x.time)-Date.parse(g.commence_time))<60000&&x.name===g.event);
 if(!already&&!games.has(g.event_id))games.set(g.event_id,{event_id:g.event_id,name:g.event||'Scheduled NFL matchup',time:g.commence_time,rows:[],schedule_only:true});
}
const scheduled=Array.isArray(d.schedule_games)?d.schedule_games.filter(g=>g&&g.event_id&&Date.parse(g.commence_time)>Date.now()):[];
const covered=new Set(odds.filter(x=>Date.now()-Date.parse(x.updated_at)<=30*60000).map(x=>x.event_id));
const quoted=new Set(odds.map(x=>x.event_id));
const coverageHtml='<section aria-label="NFL full-slate prop coverage" style="border:1px solid #47617a;border-radius:10px;padding:12px;margin:12px 0"><strong>Full-slate player-prop coverage: '+covered.size+' / '+(scheduled.length||games.size)+' games</strong><p style="font-size:12px">Fresh DK/FD player props: '+covered.size+' games; published pregame quotes (including stale): '+quoted.size+' games. Stale quotes are displayed for inspection only, never as current betting recommendations. Games without prices remain visible but cannot produce betting-ready SGPs. Gold, Silver and Bronze still require validated simulation, player status, and official combined prices.</p></section>';
const publishedRows=(d.odds||[]).filter(x=>x&&x.event_id&&x.commence_time&&['draftkings','fanduel'].includes(x.bookmaker));
const upcomingPublished=publishedRows.filter(x=>Date.parse(x.commence_time)>Date.now());
const expiredPublished=publishedRows.length-upcomingPublished.length;
const sourceAge=Date.parse(d.fetched_at);
const sourceAgeMinutes=Number.isFinite(sourceAge)?Math.round((Date.now()-sourceAge)/60000):null;
const noCreditStatsNote='<p style="font-size:12px">Historical NFL player-stat archive is not verified on this deployment. No player-specific statistical simulation is claimed until that feed loads and passes schema validation.</p>';
const feedDiagnosis=games.size===0?'<section style="border:1px solid #47617a;border-radius:10px;padding:12px;margin:12px 0"><strong>No upcoming games with published DK/FD quotes</strong><p>The page cannot assemble a verified SGP without upcoming game markets. '+(expiredPublished?'The archived player feed contains '+expiredPublished+' selections for games already started or completed. ':'')+(sourceAgeMinutes===null?'Player-feed timestamp unavailable. ':'Player feed last collected '+sourceAgeMinutes+' minutes ago. ')+'This is a feed availability issue, not a prediction that there are zero NFL games.</p><p>Historical parlay legs are not a substitute for current sportsbook prices, confirmed player status, or a validated joint model.</p></section>':'';
const sections=windows.map(w=>{const gs=[...games.values()].filter(g=>windowOf(g.time)===w).sort((a,b)=>new Date(a.time)-new Date(b.time));const cards=gs.map(g=>{
if(g.rows.length===0)return '<article style="border:1px solid #385b78;border-radius:10px;padding:12px;margin:10px 0"><strong>'+esc(g.name)+'</strong><p style="font-size:13px">'+esc(formatTime(g.time))+' · SCHEDULE CONFIRMED · DK/FD QUOTES UNAVAILABLE</p>'+tierPanel(g)+existingGameSimulation(g)+noCreditPlayerProps(g)+'<p style="font-size:13px"><strong>SGP status: BLOCKED</strong> — no current player props or official combined SGP price. No betting-ready parlay can be verified for this matchup.</p></article>';
const byBook=new Map();for(const x of g.rows){const k=x.bookmaker;if(!byBook.has(k))byBook.set(k,[]);byBook.get(k).push(x)}
const options=[...byBook].map(([book,rows])=>{const unique=[...new Map(rows.map(x=>[x.player+'|'+x.market+'|'+x.selection+'|'+x.point,x])).values()];const players=new Set(unique.map(x=>x.player).filter(Boolean));return{book,unique,players:players.size}}).sort((a,b)=>b.players-a.players||b.unique.length-a.unique.length);
const coreByBook=[...byBook].map(([book,rows])=>({book,rows:rows.filter(x=>['h2h','spreads','totals'].includes(x.market))})).filter(x=>x.rows.length);const coreMarketSummary=coreByBook.length?'<details style="margin:7px 0"><summary>Verified-source game prices ('+coreByBook.reduce((n,x)=>n+x.rows.length,0)+' fresh quotes)</summary><ul>'+coreByBook.map(x=>'<li>'+esc(x.book)+': '+x.rows.slice(0,12).map(q=>esc(q.market+' '+q.selection+(q.point==null?'':' '+q.point)+' '+price(q.price))).join(' · ')+'</li>').join('')+'</ul><small>Prices are sportsbook quotes, not simulated edges or approved SGP prices. Individual legs require separate forecast validation.</small></details>':'<p style="font-size:12px">No fresh verified-source game moneyline/spread/total quotes for this matchup.</p>';const best=options[0];const calibrationMarkets=calibration?.frozen_forward_holdout?.markets||{};const eligibleMarkets=Object.entries(calibrationMarkets).filter(([,v])=>v?.eligible_for_live_use===true).map(([k])=>k);const pairs=new Map();for(const q of g.rows){if(!['Over','Under'].includes(q.selection)||!Number.isFinite(Number(q.point)))continue;const key=JSON.stringify([q.event_id,q.bookmaker,q.player,q.market,Number(q.point)]);if(!pairs.has(key))pairs.set(key,{});pairs.get(key)[q.selection]=q}const paired=[...pairs.values()].filter(p=>p.Over&&p.Under);const matched=(ledger?.forecasts||[]).filter(f=>readiness?.sports?.NFL?.fully_verified_player_recommendations===0&&calibration?.bet_eligibility==='BLOCKED'&&f.event_id===g.rows[0]?.event_id&&f.kickoff===g.time&&Number.isFinite(Date.parse(f.quoted_at))&&Number.isFinite(Date.parse(f.forecast_at))&&Date.parse(f.quoted_at)<=Date.parse(f.forecast_at)&&Date.parse(f.forecast_at)<Date.parse(f.kickoff)&&f.research_only===true&&f.betting_eligible===false&&Number.isFinite(f.model_probability)&&f.model_probability>=0&&f.model_probability<=1&&f.line!=null&&f.bookmaker&&f.player&&f.market&&g.rows.some(q=>q.player===f.player&&q.market===f.market&&Number(q.point)===Number(f.line)&&q.bookmaker===f.bookmaker&&q.event_id===f.event_id&&q.commence_time===f.kickoff&&q.selection==='Over'&&Number(q.price)===Number(f.over_odds))&&g.rows.some(q=>q.player===f.player&&q.market===f.market&&Number(q.point)===Number(f.line)&&q.bookmaker===f.bookmaker&&q.event_id===f.event_id&&q.commence_time===f.kickoff&&q.selection==='Under'&&Number(q.price)===Number(f.under_odds))).sort((a,b)=>Date.parse(b.forecast_at)-Date.parse(a.forecast_at));const distinct=[...matched.reduce((m,f)=>{const key=f.player+'|'+f.market+'|'+f.line+'|'+f.bookmaker;if(!m.has(key))m.set(key,f);return m},new Map()).values()];/* Fail closed: only independently validated same-event/market/line/side forecasts may produce betting recommendations. */const legs=[];const sideCoverage=best?best.unique.reduce((a,x)=>(['Over','Under'].includes(x.selection)&&(a[x.selection]=(a[x.selection]||0)+1),a),{Over:0,Under:0}):{Over:0,Under:0};
const forecastResearchLegs=distinct.slice(0,3).map(f=>({player:f.player,market:f.market,point:Number(f.line),selection:f.model_probability<0.5?'Under':'Over'}));
const historicalCandidates=stats&&window.KSLNFLStats?paired.filter(p=>p.Over.bookmaker===best?.book).map(p=>{const q=p.Over;const over=window.KSLNFLStats.lookup(stats,q.player,q.market,q.point,'Over');const under=window.KSLNFLStats.lookup(stats,q.player,q.market,q.point,'Under');if(over.status!=='HISTORICAL_ONLY'||under.status!=='HISTORICAL_ONLY'||over.games<5||under.games<5)return null;const side=over.hits>=under.hits?'Over':'Under';const hit=side==='Over'?over:under;return{player:q.player,market:q.market,point:Number(q.point),selection:side,hits:hit.hits,games:hit.games,rate:hit.rate,bookmaker:q.bookmaker}}).filter(Boolean).sort((a,b)=>b.rate-a.rate||b.games-a.games):[];
const researchLegs=forecastResearchLegs.length>=2?forecastResearchLegs:historicalCandidates.slice(0,3);
/* Historical game logs can describe observed opportunity but cannot establish
 * upcoming snap/route projections or current injury verification. */
const opportunityAudit=researchLegs.map(x=>{
 const targets=stats&&window.KSLNFLStats?window.KSLNFLStats.lookup(stats,x.player,'player_targets',0,'Over'):null;
 const carries=stats&&window.KSLNFLStats?window.KSLNFLStats.lookup(stats,x.player,'player_rush_attempts',0,'Over'):null;
 return {player:x.player,targets:targets?.status==='HISTORICAL_ONLY'?targets.mean:null,carries:carries?.status==='HISTORICAL_ONLY'?carries.mean:null};
});
const researchOrigin=forecastResearchLegs.length>=2?'ARCHIVED FORECASTS':'HISTORICAL GAME LOGS';const simulationReady=!!(stats&&window.KSLSGPJoint&&typeof window.KSLSGPJoint.joint==='function');const researchJoint=stats&&window.KSLSGPJoint&&researchLegs.length>=2?window.KSLSGPJoint.joint(stats,researchLegs):{status:'BLOCKED',reason:'Need 2+ exact matched archived forecasts and historical stats'};const supported=sgpLegCountValid(legs)&&sgpSameGame(legs)&&sgpNoConflictingSelections(legs);const joint=stats&&window.KSLSGPJoint&&legs.length>=2?window.KSLSGPJoint.joint(stats,legs):{status:'BLOCKED',reason:'Verified stats or simulation engine unavailable'};const statChecks=legs.map(x=>({leg:x,result:stats?window.KSLNFLStats.lookup(stats,x.player,x.market,x.point,x.selection):{status:'UNAVAILABLE',reason:'Verified stat feed unavailable'}}));const playerCount=best?best.players:0;const marketCount=best?new Set(best.unique.map(x=>x.market)).size:0;const coverageScore=Math.min(100,Math.round(40*Math.min(playerCount/8,1)+35*Math.min(marketCount/5,1)+25*Math.min((best?.unique.length||0)/30,1)));const coverageTier=coverageScore>=85?'HIGH':coverageScore>=60?'MODERATE':'LOW';
const quoteTimes=g.rows.map(x=>Date.parse(x.updated_at)).filter(Number.isFinite);const newest=quoteTimes.length?Math.max(...quoteTimes):NaN;const age=Number.isFinite(newest)?Math.max(0,Math.round((Date.now()-newest)/60000)):null;const fresh=age!==null&&age<=30;const freshness=age===null?'QUOTE TIME UNKNOWN':age<=30?'RECENT QUOTE ('+age+'m)':age<=120?'AGING QUOTE ('+age+'m)':'STALE QUOTE ('+age+'m)';
const blockers=[!simulationReady?'JOINT_ENGINE_OR_STATS_NOT_LOADED':null,eligibleMarkets.length===0?'NO_CALIBRATED_MARKETS_ELIGIBLE':null,paired.length===0?'NO_COMPLETE_TWO_WAY_QUOTES':null,!fresh?'ODDS_STALE_OR_TIMESTAMP_MISSING':null,distinct.length===0?'NO_EXACT_TWO_WAY_FORECAST_MATCH':null,'NO_VALIDATED_PREGAME_LEG_FORECASTS','NO_CALIBRATED_JOINT_SIMULATION','NO_VERIFIED_COMBINED_SGP_PRICE','PLAYER_STATUS_UNVERIFIED'].filter(Boolean);
return '<article style="border:1px solid #385b78;border-radius:10px;padding:12px;margin:10px 0"><strong>'+esc(g.name)+'</strong><div style="opacity:.8;font-size:13px">'+esc(formatTime(g.time))+' · '+g.rows.length+' quoted selections · '+options.map(o=>esc(o.book)+' '+o.unique.length+' lines').join(' / ')+'</div><div style="font-size:12px;margin-top:6px">Market coverage: <strong>'+coverageTier+' ('+coverageScore+'/100)</strong> · '+playerCount+' players · '+marketCount+' markets · Over quotes '+sideCoverage.Over+' / Under quotes '+sideCoverage.Under+'. Coverage is NOT a win-probability grade. Complete same-book Over/Under pairs: '+paired.length+'. Calibration-eligible markets: '+eligibleMarkets.length+'. Joint research engine: '+(simulationReady?'LOADED':'UNAVAILABLE')+'.</div>'+tierPanel(g,paired,researchLegs,researchJoint)+calibrationAudit(calibration)+coreMarketSummary+existingGameSimulation(g)+'<details><summary>Historical model direction audit ('+distinct.length+' exact two-way quote matches; RESEARCH ONLY)</summary><ul>'+distinct.slice(0,12).map(f=>'<li>'+esc(f.player)+' '+esc(label[f.market]||f.market)+' '+esc(f.line)+' · '+(f.model_probability>.5?'Historical lean: OVER':f.model_probability<.5?'Historical lean: UNDER':'No historical lean')+' · model over '+(100*f.model_probability).toFixed(1)+'% · '+esc(f.bookmaker)+' · NOT BET ELIGIBLE</li>').join('')+'</ul><small>Historical 2025 model only; quote-matched, not independently calibrated or roster-verified. Not a recommendation.</small>'+(researchJoint.status==='EXPERIMENTAL'&&Number.isFinite(researchJoint.joint_rate)&&researchJoint.trials>=1000?'<p style="font-size:12px"><strong>Simulated historical research stack · '+esc(researchOrigin)+' (NOT BET ELIGIBLE):</strong></p><ol>'+researchLegs.map(x=>'<li>'+esc(x.player)+' — '+esc(label[x.market]||x.market)+' '+esc(x.selection)+' '+esc(x.point)+(x.hits==null?'':' · '+x.hits+'/'+x.games+' historical hits')+'</li>').join('')+'</ol>':'<p style="font-size:12px">No simulation-qualified historical research stack available.</p>')+'<p style="font-size:12px"><strong>Observed opportunities (historical only):</strong></p><ul>'+opportunityAudit.map(o=>'<li>'+esc(o.player)+' · targets/game '+(o.targets==null?'unavailable':o.targets.toFixed(1))+' · carries/game '+(o.carries==null?'unavailable':o.carries.toFixed(1))+' · future usage UNVERIFIED</li>').join('')+'</ul>'+'<p style="font-size:12px">Historical paired-week bootstrap: '+(researchJoint.status==='EXPERIMENTAL'?'EXPERIMENTAL · '+researchJoint.trials+' trials · '+researchJoint.paired_weeks+' paired weeks · historical joint hit rate '+(100*researchJoint.joint_rate).toFixed(1)+'% (NOT a forecast or SGP EV)':esc(researchJoint.status+' — '+researchJoint.reason))+'</p><small>Calendar-week pairs may involve different opponents; no verified same-game correlation, injury-adjusted projection, or official SGP quote. NOT BET ELIGIBLE.</small></details><div style="font-size:12px;margin-top:6px;font-weight:700">'+esc(freshness)+' · '+(fresh?'Odds freshness check passed':'Refresh sportsbook prices before use')+'</div><p style="margin:8px 0">'+(supported?'Model-validated SGP candidates:':'NO VERIFIED 1–5 LEG SELECTIONS — every leg requires a verified same-game, same-line forecast and sportsbook quote')+'</p>'+(legs.length?'<ul style="margin:6px 0;padding-left:22px">'+legs.map(x=>'<li>'+esc(x.player)+' — '+esc(label[x.market]||x.market)+' '+esc(x.selection)+(x.point==null?'':' '+esc(x.point))+' ('+esc(price(x.price))+', '+esc(x.bookmaker)+')</li>').join('')+'</ul><p style="font-size:12px"><strong>Verified game-log inputs (last 10):</strong></p><ul>'+statChecks.map(x=>'<li>'+esc(x.leg.player)+' — '+(x.result.status==='HISTORICAL_ONLY'?esc(x.result.hits+'/'+x.result.games+' historical hits; average '+x.result.mean.toFixed(1)+'; '+x.result.source):esc(x.result.reason))+'</li>').join('')+'</ul><details><summary style="cursor:pointer">Game-script stress audit (qualitative)</summary><ul>'+scriptAudit(legs).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul><p>RB receiving and rushing workloads must be forecast separately. No validated joint simulation is available.</p></details>':'')+'<p style="font-size:12px"><strong>Joint historical bootstrap:</strong> '+(joint.status==='EXPERIMENTAL'?(100*joint.joint_rate).toFixed(1)+'% sample frequency across '+joint.paired_weeks+' common weeks / '+joint.trials+' draws — NOT a calibrated SGP probability':esc(joint.reason))+'</p><small>Betting grade: BLOCKED (unvalidated) · Joint simulation: HISTORICAL RESEARCH ONLY · Combined SGP quote: NOT VERIFIED · EV: NOT CALCULABLE · Player status: NOT VERIFIED · Betting eligibility: NO. Individual-leg prices cannot establish an SGP price or correlation-adjusted win probability.</small></article>'}).join('');
return '<details '+(gs.length?'open':'')+'><summary style="cursor:pointer;font-weight:700;padding:10px 0">'+esc(w)+' — '+gs.length+' scheduled / quoted games ('+gs.filter(g=>g.rows.length>0).length+' with DK/FD markets)</summary>'+(cards||'<p>No fresh supported DK/FD markets published for this window yet.</p>')+'</details>'}).join('');
const timestamp=d.fetched_at?new Date(d.fetched_at).toLocaleString('en-US',{timeZone:'America/New_York',timeZoneName:'short'}):'unknown';
root.innerHTML='<h2>🏈 NFL SGP Stack Finder</h2><p style="font-size:11px;opacity:.75">SGP display build: 20261109-pr865 · Published odds only · No API request from this page</p>'+coverageHtml+'<button id="nfl-sgp-refresh" type="button" style="display:block;width:100%;padding:13px 14px;margin:10px 0 12px;background:#176b54;color:white;border:1px solid #55c9a1;border-radius:9px;font-weight:800">↻ Refresh SGP screen (published odds)</button><p style="font-size:12px;margin:0 0 12px;color:#b6c8d9">Reloads the published DK/FD feed; it does not collect new prices. To fetch live provider quotes, <a href="https://github.com/Donovan1019/kennys-sports-lab-mobile/actions/workflows/refresh-nfl-props.yml" target="_blank" rel="noopener noreferrer" style="color:#8de7ff;text-decoration:underline">run the NFL props collection workflow</a> (Run workflow → max_events 16), then reload this screen after it succeeds. Stale or unverified selections remain blocked.</p><p><strong>Automatic window discovery:</strong> Thursday, Sunday morning / 1 PM / 4 PM / night, Monday, and special games. Source refreshed '+esc(timestamp)+'. <strong>RESEARCH ONLY.</strong></p><p>This screen shows which sportsbook markets exist, NOT which side to bet. No SGP legs are recommended until an independently validated forecast checks BOTH Over and Under at the exact game, player, market and line. Missing model validation means BLOCKED, even if sportsbook odds are available. Correlation-adjusted probability, official SGP price, EV and player availability also require verification.</p>'+readinessDiagnostics(d,readiness,calibration)+feedDiagnosis+'<div>'+sections+'</div>';
document.getElementById('nfl-sgp-refresh').addEventListener('click',load)}
async function load(){root.innerHTML='<h2>🏈 NFL SGP Stack Finder</h2><p>Loading published DK/FD player markets…</p>';try{const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),12000);let odds;try{const r=await fetch('./feed/nfl_props.json?ts='+Date.now(),{cache:'no-store',signal:controller.signal});if(!r.ok)throw Error('Odds feed HTTP '+r.status);odds=await r.json()}finally{clearTimeout(timer)}let ledger=null;try{const lr=await fetch('./feed/nfl_prop_forecast_ledger.json?ts='+Date.now(),{cache:'no-store',signal:controller.signal});if(lr.ok)ledger=await lr.json()}catch(e){console.warn('SGP historical forecast ledger unavailable:',e.message)}let readiness=null,calibration=null;try{const checks=await Promise.all(['./feed/player_recommendation_readiness.json','./feed/nfl_sgp_walkforward_accuracy.json'].map(path=>fetch(path+'?ts='+Date.now(),{cache:'no-store',signal:controller.signal})));if(checks[0].ok)readiness=await checks[0].json();if(checks[1].ok)calibration=await checks[1].json()}catch(e){console.warn('SGP readiness unavailable:',e.message)}let coreOdds=[];for(const path of ['./feed/americanfootball_nfl.json']){try{const cr=await fetch(path+'?ts='+Date.now(),{cache:'no-store'});if(!cr.ok)continue;const cd=await cr.json();if(['the-odds-api-v4-core-markets','the-odds-api-v4'].includes(cd.source)&&cd.sport==='americanfootball_nfl'&&Array.isArray(cd.odds))coreOdds.push(...cd.odds)}catch(e){console.warn('NFL SGP core-market feed unavailable:',path,e.message)}}odds.core_odds=coreOdds;
let scheduleGames=[];
try{
 const sr=await fetch('./feed/independent_game_inputs.json?ts='+Date.now(),{cache:'no-store'});
 if(sr.ok){
  const sd=await sr.json();
  if(sd.source==='ESPN public scoreboard'&&Array.isArray(sd.games))scheduleGames=sd.games.map(g=>({event_id:g.event_id,event:g.event,commence_time:g.commence_time}));
 }
}catch(e){console.warn('NFL schedule unavailable:',e.message)}
// Prefer the sportsbook event IDs already attached to the published prop quotes.
 // ESPN uses different event IDs; use it only to fill genuinely missing matchups.
 const providerSchedule=Array.isArray(odds.schedule_games)?odds.schedule_games:[];
 const normalize=x=>String(x||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
 const matchKey=g=>normalize(g.event)+'|'+String(Date.parse(g.commence_time)||'');
 const known=new Set(providerSchedule.map(matchKey));
 odds.schedule_games=providerSchedule.concat(scheduleGames.filter(g=>!known.has(matchKey(g))));
render(odds,null,ledger,readiness,calibration);if(!window.KSLNFLStats)return;try{const stats=await Promise.race([window.KSLNFLStats.load(),new Promise((_,reject)=>setTimeout(()=>reject(Error('Stats request timed out')),8000))]);render(odds,stats,ledger,readiness,calibration)}catch(e){console.warn('SGP historical stats unavailable:',e.message)}}catch(e){root.innerHTML='<h2>🏈 NFL SGP Stack Finder</h2><p>Market coverage unavailable: '+esc(e.name==='AbortError'?'Odds request timed out':e.message)+'. No betting recommendations can be verified.</p><button id="nfl-sgp-retry" type="button">Retry loading</button>';document.getElementById('nfl-sgp-retry').onclick=load}}
// A long-lived mobile tab must not continue showing yesterday's matchups.
let lastResumeRefresh=0;
function refreshOnResume(){
 if(document.visibilityState==='hidden'||Date.now()-lastResumeRefresh<60000)return;
 lastResumeRefresh=Date.now();
 load();
}
document.addEventListener('visibilitychange',refreshOnResume);
window.addEventListener('focus',refreshOnResume);
if(!window.KSLNFLStats){const script=document.createElement('script');script.src='./nfl_sgp_verified_stats.js';script.onload=load;script.onerror=load;document.head.append(script)}else load();
})();
