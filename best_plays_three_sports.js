/* Three sport-specific, evidence-gated Best Plays boards. No synthetic picks. */
(()=>{'use strict';
const config=[
 {sport:'NFL',id:'ksl-nfl-best-plays',feed:'americanfootball_nfl',markets:'Moneyline · spread · totals · QB passing · rushing · receiving · touchdowns · team totals'},
 {sport:'NBA',id:'ksl-nba-best-plays',feed:'basketball_nba',markets:'Moneyline · spread · totals · points · rebounds · assists · PRA'},
 {sport:'NHL',id:'ksl-nhl-best-plays',feed:'icehockey_nhl',markets:'Moneyline · puck line · totals · shots on goal · goalie saves · team totals'}
];
const marketCatalog={
 NFL:['Moneyline','Spread','Alternate Spreads','Game Total','Alternate Game Totals','Team Totals','Alternate Team Totals','1H / 2H','1H / 2H Team Totals','Quarters','Quarter Team Totals','First Score / First TD','First Drive / Drive Results','Race to Points','Winning Margin','QB Passing Yards','QB Passing TDs','QB Completions / Attempts','QB Interceptions','QB Passing + Rushing','QB Rushing','RB Rushing Yards','RB Rushing Attempts','RB Receiving','RB Rushing + Receiving','WR / TE Receiving Yards','Receptions','Longest Pass / Rush / Reception','Anytime TD','First / Last TD','Multiple TDs','Kicker Points / FGs','Defense / Specials','Sacks / Tackles','Live / Halftime','SGP / Builders','Kenny’s SGP','SGP Magic / Halftime Magic','Futures'],
 NBA:['Moneyline','Spread','Alternate Spreads','Game Total','Alternate Game Totals','Team Totals','Alternate Team Totals','1H / 2H','1H / 2H Team Totals','Quarters','Quarter Team Totals','Race to Points','Winning Margin','First Basket / First Team Basket','Player Points','Player Rebounds','Player Assists','P+R / P+A / R+A / PRA','Threes Made','Threes Attempted','Steals / Blocks','Turnovers','Player Minutes','Field Goals / Free Throws','Double-Doubles','Triple-Doubles','Player First Basket','Player 1Q / 1H Props','Player Milestones / Alternates','Top Scorer / Matchup Props','Live / Halftime','SGP / Builders','SGP Magic / Halftime Magic','Futures'],
 NHL:['Moneyline','3-Way Regulation','Puck Line','Alternate Puck Lines','Game Total','Alternate Game Totals','Team Totals','Alternate Team Totals','1P / 2P / 3P','Period Team Totals','Period 3-Way / Puck Lines','Race to Goals','First / Last Goal Team','Winning Margin','Overtime / Shootout','Player Shots on Goal','Alternate Shots on Goal','Goalie Saves','Alternate Goalie Saves','Player Points / Assists','Player Goals','Anytime Goal','First / Last Goal Scorer','Multiple Goals / Hat Trick','Blocked Shots','Power Play','Player Power-Play Points','Faceoff Wins','Goalie Shutout','Live / Intermission','SGP / Builders','SGP Magic / Intermission Magic','Futures']
};
// Deterministic empirical resampling of completed games. Descriptive only, NOT calibrated forecasts.
function historyBootstrap(values,threshold,trials=10000){
 if(!Array.isArray(values)||values.length<3||values.some(x=>!Number.isFinite(x)||x<0))return null;
 let state=20261021,over=0;
 for(let i=0;i<trials;i++){state=(Math.imul(1664525,state)+1013904223)>>>0;const sample=values[Math.floor((state/4294967296)*values.length)];if(sample>threshold)over++;}
 return over/trials;
}
const main=document.querySelector('main');if(!main)return;
const safe=(value)=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const style=document.createElement('style');style.textContent='.ksl-best-plays{border:1px solid #397c65;border-radius:14px;background:linear-gradient(140deg,#102c24,#0b1b2b);padding:16px;margin:14px 0 20px}.ksl-best-plays h2{color:#99f4ba;margin:0 0 8px}.ksl-best-plays p{font-size:13px;color:#bed3cb;line-height:1.55}.ksl-best-plays .ksl-best-pass{border:1px solid #775d36;background:#332b1d;color:#ffe2a0;border-radius:9px;padding:12px;font-weight:800;margin:12px 0}.ksl-best-plays .ksl-best-meta{font-size:12px;color:#a6c1bc}.ksl-best-plays button{min-height:40px}.ksl-best-plays .ksl-best-row{border:1px solid #315d51;border-radius:9px;padding:12px;margin:10px 0;background:#0c211d}.ksl-best-plays .ksl-best-row strong{color:#b6ffd1}'.concat('.ksl-best-market-browser{border:1px solid #315b55;border-radius:10px;padding:12px;margin:12px 0;background:#0c2024}.ksl-best-market-browser h3{margin:0 0 6px;color:#a3efc3}.ksl-best-market-browser select{width:100%;max-width:100%;min-height:45px}.ksl-best-market-state{padding:9px;border-radius:8px;background:#172c31;color:#f1d59c!important}');document.head.append(style);
for(const cfg of config){
 const panel=document.createElement('section');panel.id=cfg.id;panel.className='ksl-best-plays';panel.dataset.sport=cfg.sport;
 panel.innerHTML='<h2>'+cfg.sport+' · Best Plays Lab</h2><p>Sport-specific model research and market verification. Markets: '+cfg.markets+'.</p><div class="ksl-best-pass" role="status">NO VERIFIED PLAY — awaiting eligible data</div><div class="ksl-best-results"></div><p class="ksl-best-meta">Diamond Plays, safer builders and SGP candidates require verified odds, calibrated probabilities, relevant lineup/injury checks, and simulation evidence. Historical trends alone do not qualify.</p><button type="button" class="ksl-best-reload">Refresh research</button>';
 main.append(panel);
 // Market coverage navigator: available market categories do not imply verified betting quotes.
 const browser=document.createElement('div');browser.className='ksl-best-market-browser';
 const heading=document.createElement('h3');heading.textContent='All markets · '+cfg.sport;browser.append(heading);
 const expl=document.createElement('p');expl.textContent='Select a market to see its current research availability. Listed markets are coverage targets, not confirmed Onyx offerings.';browser.append(expl);
 const picker=document.createElement('select');picker.setAttribute('aria-label',cfg.sport+' market category');
 for(const name of marketCatalog[cfg.sport]){const option=document.createElement('option');option.value=name;option.textContent=name;picker.append(option);}
 browser.append(picker);
 const marketState=document.createElement('p');marketState.className='ksl-best-market-state';marketState.setAttribute('role','status');browser.append(marketState);
 const integrity=document.createElement('p');integrity.className='ksl-best-market-state';integrity.setAttribute('role','status');integrity.textContent='Checking player-prop input integrity…';browser.append(integrity);
 function updateMarket(){
  const name=picker.value;
  marketState.textContent=(cfg.sport==='NHL'&&['Player Shots on Goal','Goalie Saves','Player Points / Assists','Anytime Goal'].includes(name)?'OFFICIAL NHL HISTORICAL STATS · no current prop odds or simulations.':cfg.sport==='NFL'&&nflPropCategories[name]?'ARCHIVED REFERENCE QUOTES ONLY · historical external-book prices; not live, no verified model edge.':name==='Moneyline'?'MONEYLINE · archived model-versus-consensus research below. Live price, simulation and eligibility remain unverified.':'DATA NOT CONNECTED · '+name+' has no event-matched, verified odds/projection/simulation feed in this Best Plays module. Not an available pick.');
 }
 picker.addEventListener('change',()=>{updateMarket();renderMarket();});
 panel.insertBefore(browser,panel.querySelector('.ksl-best-pass'));
 const status=panel.querySelector('.ksl-best-pass'),results=panel.querySelector('.ksl-best-results');
 let currentEvents=[],currentConsensus=null,currentAsOf=null;
 let archivedProps=null,nhlHistory=null,playerHistory=null;
 const nflPropCategories={
  'QB Passing Yards':['player_pass_yds'],'QB Passing TDs':['player_pass_tds'],
  'RB Rushing Yards':['player_rush_yds'],'QB Rushing':['player_rush_yds'],
  'RB Receiving':['player_reception_yds','player_receptions'],
  'WR / TE Receiving Yards':['player_reception_yds'],'Receptions':['player_receptions'],
  'Anytime TD':['player_anytime_td']
 };

 updateMarket();

 function renderMarket(){
  results.replaceChildren();const name=picker.value;
  const nhlStatFields={'Player Shots on Goal':'Shots on goal','Goalie Saves':'Saves','Player Points / Assists':'Points','Anytime Goal':'Goals'};
  const nflFields={'QB Passing Yards':'Passing yards','QB Passing TDs':'Passing touchdowns','RB Rushing Yards':'Rushing yards','QB Rushing':'Rushing yards','WR / TE Receiving Yards':'Receiving yards','Receptions':'Receptions','Anytime TD':'Receiving touchdowns'};
  const nbaFields={'Player Points':'Points','Player Rebounds':'Rebounds','Player Assists':'Assists','Threes Made':'3-pointers made'};
  const historyField=cfg.sport==='NFL'?nflFields[name]:cfg.sport==='NBA'?nbaFields[name]:null;
  if(historyField){
   const players=(playerHistory?.players||[]).map(p=>{
    const games=(p.games||[]).filter(g=>Number.isFinite(g.values?.[historyField])&&g.values[historyField]>=0).sort((a,b)=>cfg.sport==='NFL'?(b.season-a.season)||(b.week-a.week):String(b.date).localeCompare(String(a.date))).slice(0,5);
    return {p,games,avg:games.length?games.reduce((sum,g)=>sum+g.values[historyField],0)/games.length:0};
   }).filter(x=>x.games.length>=3).sort((a,b)=>b.avg-a.avg).slice(0,15);
   const h=document.createElement('h3');h.textContent=name+' · observed player game logs';results.append(h);
   const note=document.createElement('p');note.textContent='10,000-draw empirical bootstrap of up to five past games. Illustrative historical resampling ONLY, not a forecast, current line, Onyx availability, or bet recommendation.';results.append(note);
   if(!players.length){const msg=document.createElement('p');msg.textContent='No usable player game logs for this market. DATA NOT CONNECTED.';results.append(msg);return;}
   for(const x of players){
    const row=document.createElement('div');row.className='ksl-best-row';
    const title=document.createElement('strong');title.textContent=x.p.name+' ('+x.p.team+') · '+x.avg.toFixed(1)+' '+historyField+' / game';row.append(title);
    const vals=x.games.map(g=>g.values[historyField]);const threshold=Math.floor(x.avg)+0.5;
    const rate=historyBootstrap(vals,threshold);
    const info=document.createElement('p');info.textContent='Last '+vals.length+' observations: '+vals.join(', ')+' · 10,000 historical draws above illustrative '+threshold+': '+(rate*100).toFixed(1)+'%. NOT BET ELIGIBLE.';row.append(info);results.append(row);
   }
   return;
  }
  if(cfg.sport==='NHL'&&nhlStatFields[name]){
   const metric=nhlStatFields[name];const players=(nhlHistory?.players||[]).map(p=>{
    const games=(p.games||[]).filter(g=>Number.isFinite(g.values?.[metric])&&!(g.quality_flags||[]).length).sort((a,b)=>String(b.date).localeCompare(String(a.date))).slice(0,5);
    return {p,games,avg:games.length?games.reduce((sum,g)=>sum+g.values[metric],0)/games.length:null};
   }).filter(x=>x.games.length>=3).sort((a,b)=>b.avg-a.avg).slice(0,20);
   const heading=document.createElement('h3');heading.textContent=name+' · official NHL historical stats';results.append(heading);
   const warning=document.createElement('p');warning.textContent='Historical completed-game statistics only. Ranked by last-five observed average, not projected hit probability or EV. No verified prop line or Onyx availability. NOT BET ELIGIBLE.';results.append(warning);
   const meta=document.createElement('p');meta.textContent='Official NHL archive collected '+(nhlHistory?.fetched_at?new Date(nhlHistory.fetched_at).toLocaleString():'unknown')+' · minimum 3 recorded games';results.append(meta);
   if(!players.length){const empty=document.createElement('p');empty.textContent='No verified historical observations available for '+metric+'.';results.append(empty);return;}
   for(const x of players){const row=document.createElement('div');row.className='ksl-best-row';const title=document.createElement('strong');title.textContent=x.p.name+' ('+x.p.team+') · '+x.avg.toFixed(2)+' '+metric+' / game';row.append(title);const detail=document.createElement('p');detail.textContent='Recent '+x.games.length+' games: '+x.games.map(g=>g.values[metric]).join(', ')+' | '+x.games[0].date+' latest';row.append(detail);
    if(metric==='Shots on goal'||metric==='Saves'){
     const threshold=metric==='Shots on goal'?2.5:24.5;
     const rate=historyBootstrap(x.games.map(g=>g.values[metric]),threshold);
     if(rate!==null){const sim=document.createElement('p');sim.textContent='10,000-draw historical bootstrap: '+(rate*100).toFixed(1)+'% of resamples exceeded '+threshold+'. NOT a projected hit rate, verified line, or betting edge.';row.append(sim);}
    }
    results.append(row);}
   return;
  }
  if(cfg.sport==='NFL'&&nflPropCategories[name]){
   const matches=(archivedProps?.odds||[]).filter(q=>nflPropCategories[name].includes(q.market));
   const heading=document.createElement('h3');heading.textContent=name+' · archived reference quotes';results.append(heading);
   const warning=document.createElement('p');warning.textContent='Historical external-book snapshots only, NOT current or verified Onyx availability. These are quoted lines, not projections, simulations, or betting recommendations.';results.append(warning);
   if(!matches.length){const empty=document.createElement('p');empty.textContent='No archived reference quotes for this market.';results.append(empty);return;}
   const date=document.createElement('p');date.textContent='Snapshot: '+(archivedProps?.fetched_at?new Date(archivedProps.fetched_at).toLocaleString():'unknown')+' · '+matches.length+' quote rows';results.append(date);
   for(const q of matches.slice(0,30)){
    const row=document.createElement('div');row.className='ksl-best-row';
    const title=document.createElement('strong');title.textContent=(q.player||'Unknown player')+' · '+(q.selection||'')+(q.point==null?'':' '+q.point);row.append(title);
    const details=document.createElement('p');details.textContent=(q.event||'Event unverified')+' | '+(q.bookmaker||'unknown book')+' '+(q.price>0?'+':'')+q.price+' | '+(q.updated_at||'quote time unknown');row.append(details);results.append(row);
   }
   if(matches.length>30){const more=document.createElement('p');more.textContent='Showing first 30 quotes of '+matches.length+'; no player-level filtering or bet ranking yet.';results.append(more);}
   return;
  }
  if(name!=='Moneyline'){
   const message=document.createElement('p');message.textContent=name+' · no verified event-matched market lines, prices, and projections have been published to this module. Selection remains unavailable; other market research elsewhere on this site does not establish betting eligibility.';results.append(message);return;
  }
  const byId=new Map((currentConsensus?.events||[]).map(x=>[x.event_id,x]));
  const ranked=currentEvents.map(e=>{const c=byId.get(e.event_id),p=e.model_probability,q=c?.home_consensus_no_vig;if(!Number.isFinite(p)||!Number.isFinite(q)||p<=0||p>=1||q<=0||q>=1)return null;const diff=(p-q)*100;return {e,c,side:diff>=0?'home':'away',gap:Math.abs(diff)};}).filter(Boolean).sort((a,b)=>b.gap-a.gap).slice(0,5);
  if(!ranked.length){results.textContent='No matched model and archived consensus records for moneylines.';return;}
  const title=document.createElement('h3');title.textContent='Moneyline · model vs archived market';results.append(title);
  const caution=document.createElement('p');caution.textContent='Research-only gaps; not expected value, live prices, or validated picks. NOT BET ELIGIBLE.';results.append(caution);
  for(const r of ranked){const row=document.createElement('div');row.className='ksl-best-row';const label=document.createElement('strong');label.textContent=(r.side==='home'?r.e.home:r.e.away)+' · research lean';row.append(label);const detail=document.createElement('p');detail.textContent=r.e.away+' @ '+r.e.home+' | model '+(100*(r.side==='home'?r.e.model_probability:1-r.e.model_probability)).toFixed(1)+'% | archived consensus '+(100*(r.side==='home'?r.c.home_consensus_no_vig:1-r.c.home_consensus_no_vig)).toFixed(1)+'% | difference '+r.gap.toFixed(1)+' pp | '+r.c.bookmaker_count+' books';row.append(detail);results.append(row);}
 }

 async function load(){
  status.textContent='Checking archived research…';results.replaceChildren();
  try{
   const response=await fetch('./feed/'+cfg.feed+'_pregame_research.json',{cache:'no-store'});
   if(!response.ok)throw Error('Research feed unavailable ('+response.status+')');
   const data=await response.json(),events=Array.isArray(data.events)?data.events:[];
   const eligible=events.filter(e=>e.bet_eligible===true&&e.status==='verified'&&e.verified_market===true&&e.simulation_verified===true&&Number.isFinite(e.hit_probability)&&Number.isFinite(e.market_odds_american)&&Number.isFinite(e.expected_value)&&e.expected_value>0);
   status.textContent=eligible.length?'VERIFIED CANDIDATES — review market freshness':'NO VERIFIED PLAY — '+events.length+' researched matchup'+(events.length===1?'':'s')+', 0 fully qualified picks';
   currentEvents=events;currentAsOf=data.asof||null;
   try{const response=await fetch('./feed/'+cfg.feed+'_market_consensus.json',{cache:'no-store'});currentConsensus=response.ok?await response.json():null;}catch(err){currentConsensus=null;}
   if((cfg.sport==='NFL'||cfg.sport==='NBA')&&!playerHistory){
    try{const file=cfg.sport==='NFL'?'nfl_player_stats.json':'nba_player_stats.json';const p=await fetch('./feed/'+file,{cache:'no-store'});playerHistory=p.ok?await p.json():null;}catch(err){playerHistory=null;}
   }
   if(cfg.sport==='NHL'&&!nhlHistory){try{const p=await fetch('./feed/nhl_official_player_stats.json',{cache:'no-store'});nhlHistory=p.ok?await p.json():null;}catch(err){nhlHistory=null;}}
   if(cfg.sport==='NFL'&&!archivedProps){try{const p=await fetch('./feed/nfl_props.json',{cache:'no-store'});archivedProps=p.ok?await p.json():null;}catch(err){archivedProps=null;}}
   try{
    const response=await fetch('./feed/player_recommendation_readiness.json',{cache:'no-store'});
    if(response.ok){
     const report=await response.json(),audit=report.sports?.[cfg.sport];
     if(audit){
      const n=audit.fully_verified_player_recommendations||0;
      integrity.textContent='PLAYER-PROP READINESS · '+n+' verified recommendations · '+(audit.researched_events||0)+' researched events · lineup verification, fresh prices, calibrated simulations and EV must all pass before picks.';
     }else integrity.textContent='PLAYER-PROP READINESS · no sport audit available. No verified recommendations.';
    }else integrity.textContent='PLAYER-PROP READINESS · audit not published; no verified recommendations.';
   }catch(err){integrity.textContent='PLAYER-PROP READINESS · audit unavailable; no verified recommendations.';}
   renderMarket();
   const meta=panel.querySelector('.ksl-best-meta');meta.textContent='Archived research as of '+(data.asof?new Date(data.asof).toLocaleString():'unknown')+'. Not live sportsbook pricing. Diamond Plays, builders, and SGP remain unavailable until all required inputs are verified.';
  }catch(error){status.textContent='NO VERIFIED PLAY — research feed unavailable';results.textContent=error.message;}
 }
 panel.querySelector('button').addEventListener('click',load);load();
}
})();