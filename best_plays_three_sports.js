/* Three sport-specific, evidence-gated Best Plays boards. No synthetic picks. */
(()=>{'use strict';
const config=[
 {sport:'NFL',id:'ksl-nfl-best-plays',feed:'americanfootball_nfl',markets:'Moneyline · spread · totals · QB passing · rushing · receiving · touchdowns · team totals'},
 {sport:'NBA',id:'ksl-nba-best-plays',feed:'basketball_nba',markets:'Moneyline · spread · totals · points · rebounds · assists · PRA'},
 {sport:'NHL',id:'ksl-nhl-best-plays',feed:'icehockey_nhl',markets:'Moneyline · puck line · totals · shots on goal · goalie saves · team totals'}
];
const main=document.querySelector('main');if(!main)return;
const safe=(value)=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const style=document.createElement('style');style.textContent='.ksl-best-plays{border:1px solid #397c65;border-radius:14px;background:linear-gradient(140deg,#102c24,#0b1b2b);padding:16px;margin:14px 0 20px}.ksl-best-plays h2{color:#99f4ba;margin:0 0 8px}.ksl-best-plays p{font-size:13px;color:#bed3cb;line-height:1.55}.ksl-best-plays .ksl-best-pass{border:1px solid #775d36;background:#332b1d;color:#ffe2a0;border-radius:9px;padding:12px;font-weight:800;margin:12px 0}.ksl-best-plays .ksl-best-meta{font-size:12px;color:#a6c1bc}.ksl-best-plays button{min-height:40px}.ksl-best-plays .ksl-best-row{border:1px solid #315d51;border-radius:9px;padding:12px;margin:10px 0;background:#0c211d}.ksl-best-plays .ksl-best-row strong{color:#b6ffd1}';document.head.append(style);
for(const cfg of config){
 const panel=document.createElement('section');panel.id=cfg.id;panel.className='ksl-best-plays';panel.dataset.sport=cfg.sport;
 panel.innerHTML='<h2>'+cfg.sport+' · Best Plays Lab</h2><p>Sport-specific model research and market verification. Markets: '+cfg.markets+'.</p><div class="ksl-best-pass" role="status">NO VERIFIED PLAY — awaiting eligible data</div><div class="ksl-best-results"></div><p class="ksl-best-meta">Diamond Plays, safer builders and SGP candidates require verified odds, calibrated probabilities, relevant lineup/injury checks, and simulation evidence. Historical trends alone do not qualify.</p><button type="button" class="ksl-best-reload">Refresh research</button>';
 main.append(panel);
 const status=panel.querySelector('.ksl-best-pass'),results=panel.querySelector('.ksl-best-results');
 async function load(){
  status.textContent='Checking archived research…';results.replaceChildren();
  try{
   const response=await fetch('./feed/'+cfg.feed+'_pregame_research.json',{cache:'no-store'});
   if(!response.ok)throw Error('Research feed unavailable ('+response.status+')');
   const data=await response.json(),events=Array.isArray(data.events)?data.events:[];
   const eligible=events.filter(e=>e.bet_eligible===true&&e.status==='verified'&&e.verified_market===true&&e.simulation_verified===true&&Number.isFinite(e.hit_probability)&&Number.isFinite(e.market_odds_american)&&Number.isFinite(e.expected_value)&&e.expected_value>0);
   status.textContent=eligible.length?'VERIFIED CANDIDATES — review market freshness':'NO VERIFIED PLAY — '+events.length+' researched matchup'+(events.length===1?'':'s')+', 0 fully qualified picks';
   if(eligible.length){
    eligible.sort((a,b)=>b.expected_value-a.expected_value);
    for(const e of eligible.slice(0,10)){
     const row=document.createElement('div');row.className='ksl-best-row';
     row.innerHTML='<strong>'+safe(e.away)+' @ '+safe(e.home)+'</strong><p>'+safe(e.selection)+' · '+safe(e.market)+' · '+safe(e.market_odds_american)+' · Model '+(100*e.hit_probability).toFixed(1)+'% · EV '+(100*e.expected_value).toFixed(1)+'%</p>';results.append(row);
    }
   }else{
    const reasons=[...new Set(events.map(e=>e.reason).filter(Boolean))].slice(0,2);
    const info=document.createElement('p');info.textContent=reasons.length?'Why picks are withheld: '+reasons.join(' | '):'No eligible selections in the published research feed.';results.append(info);
   }
   const meta=panel.querySelector('.ksl-best-meta');meta.textContent='Archived research as of '+(data.asof?new Date(data.asof).toLocaleString():'unknown')+'. Not live sportsbook pricing. Diamond Plays, builders, and SGP remain unavailable until all required inputs are verified.';
  }catch(error){status.textContent='NO VERIFIED PLAY — research feed unavailable';results.textContent=error.message;}
 }
 panel.querySelector('button').addEventListener('click',load);load();
}
})();