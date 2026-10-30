(()=>{'use strict';
const root=document.getElementById('ufc-data-lab');if(!root)return;
const make=(tag,value)=>{const x=document.createElement(tag);if(value!==undefined)x.textContent=value;return x};
root.append(make('h2','🥊 UFC Historical Stats & Model Health'));
const intro=make('p','Saved historical results and Elo ratings, not verified current fighter form. No fabricated striking, takedown, method or round projections.');root.append(intro);
const status=make('p','Loading saved UFC research datasets…');status.setAttribute('role','status');root.append(status);
const search=make('input');search.placeholder='Search historical fighter';search.setAttribute('aria-label','Search UFC historical fighter');search.style.cssText='width:100%;max-width:400px;padding:12px;border-radius:8px;background:#10283a;color:#fff;border:1px solid #42677b';root.append(search);
const tableWrap=make('div');tableWrap.style.overflowX='auto';const table=make('table');table.style.cssText='min-width:560px;width:100%;border-collapse:collapse';const head=make('tr');for(const name of ['Fighter','Sample wins','Sample losses','Saved Elo','Prior bouts']){const th=make('th',name);th.style.padding='10px';head.append(th)}table.append(head);const body=make('tbody');table.append(body);tableWrap.append(table);root.append(tableWrap);
const audit=make('div');root.append(audit);
const get=async path=>{const response=await fetch(path,{cache:'no-store'});if(!response.ok)throw Error(path+' unavailable');return response.json()};
Promise.all([get('./feed/ufc_winner_history.json'),get('./backtests/reports/ufc_elo_baseline.json'),get('./backtests/reports/ufc_data_health.json'),get('./feed/ufc_simulations.json')]).then(([history,elo,health,sim])=>{
if(history.sport!=='UFC'||elo.sport!=='UFC'||health.sport!=='UFC'||sim.sport!=='UFC'||health.bet_eligible!==false||sim.bet_eligible!==false)throw Error('Research integrity flags invalid');
const fighters=Array.isArray(history.fighters)?history.fighters:[],ratings=elo.ratings||{};
status.textContent=history.unique_completed_fights+' saved independently scoreboard-verified winners · '+fighters.length+' fighter profiles · '+(health.holdout_n||0)+' locally evaluated holdout bouts · research only';
const draw=()=>{body.replaceChildren();const q=search.value.trim().toLowerCase();for(const f of fighters.filter(x=>x.name&&x.name.toLowerCase().includes(q)).slice(0,80)){const tr=make('tr');const rating=ratings[f.name]||{};for(const v of [f.name,String(f.wins??'—'),String(f.losses??'—'),Number.isFinite(rating.elo)?rating.elo.toFixed(1):'UNAVAILABLE',Number.isInteger(rating.historical_bouts)?String(rating.historical_bouts):'—']){const td=make('td',v);td.style.cssText='padding:10px;border-bottom:1px solid #345';tr.append(td)}body.append(tr)}};
search.addEventListener('input',draw);draw();
for(const t of ['Simulated upcoming fights: '+(Array.isArray(sim.simulations)?sim.simulations.length:0),'Blocked simulations: '+(Array.isArray(sim.blocked)?sim.blocked.length:0),'Holdout calibration: '+(health.status||'UNAVAILABLE'),'Historical source: '+history.source,'Model limitations: '+(Array.isArray(health.blockers)?health.blockers.join(', '):'unverified')])audit.append(make('p',t));

// Full-card betting-readiness audit. All fallback priors remain research-only.
const readiness=make('div');readiness.id='ufc-five-stage-audit';root.append(readiness);
const heading=make('h3','Five-stage UFC betting readiness');readiness.append(heading);
const explanation=make('p','Career coverage · opponent adjustment · sparse-data estimate · simulation · validated EV. Missing evidence is explicitly flagged, not fabricated.');readiness.append(explanation);
const refresh=make('button','↻ Refresh full-card audit');refresh.type='button';refresh.style.cssText='padding:12px 16px;background:#187a64;color:white;border-radius:9px;cursor:pointer';readiness.append(refresh);
const state=make('p','Loading full-card audit…');readiness.append(state);
const results=make('div');readiness.append(results);
const normalized=s=>String(s||'').normalize('NFKD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
const pct=p=>(p*100).toFixed(1)+'%';
async function auditFights(){
refresh.disabled=true;state.textContent='Loading verified UFC feeds…';results.replaceChildren();
try{
const [card,stats,elo,odds,baseline,history]=await Promise.all(['./feed/ufc_research.json','./feed/ufc_fighter_stats_mirror.json','./feed/ufc_elo_projections.json','./feed/mma_mixed_martial_arts.json','./backtests/reports/ufc_elo_baseline.json','./feed/ufc_winner_history.json'].map(path=>fetch(path+'?refresh='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error(path+' HTTP '+r.status);return r.json()})));
if(!Array.isArray(card.fights)||!Array.isArray(stats.fighters)||!Array.isArray(odds.odds))throw Error('Invalid source schema');
const profiles=new Map(stats.fighters.map(x=>[normalized(x.name),x]));
const elos=new Map((elo.projections||[]).map(x=>[String(x.fight_id),x]));
const records=new Map((history.fighters||[]).map(x=>[normalized(x.name),x]));
const auditMeta=make('p','Research gates: missing pre-UFC career records, missing verified opponent-specific style features, no calibrated bout-level simulation, and no point-in-time validated EV. Historical model results must not be marketed as live betting signals.');readiness.append(auditMeta);
let total=0,missing=0;
for(const f of card.fights.filter(x=>x.red&&x.blue&&Date.parse(x.start_time)>Date.now()-36*3600000)){
total++;const a=profiles.get(normalized(f.red)),b=profiles.get(normalized(f.blue)),e=elos.get(String(f.id));
const na=a?.career_round_totals?.round_rows||0,nb=b?.career_round_totals?.round_rows||0;
const both=na>0&&nb>0;if(!both)missing++;
const ea=e&&Number.isFinite(e.red_elo)&&Number.isFinite(e.blue_elo)&&normalized(e.red)===normalized(f.red)&&normalized(e.blue)===normalized(f.blue);
const strength=ea?Math.max(-.65,Math.min(.65,(e.red_elo-e.blue_elo)/500)):0;
const rate=(x,k)=>x?.career_round_totals?.round_rows>0?x.career_round_totals[k]/x.career_round_totals.round_rows:null;
const sa=rate(a,'sig_landed'),sb=rate(b,'sig_landed'),ta=rate(a,'td_landed'),tb=rate(b,'td_landed');
const strike=sa===null||sb===null?0:Math.max(-.5,Math.min(.5,Math.log((sa+3)/(sb+3))*.45));
const td=ta===null||tb===null?0:Math.max(-.3,Math.min(.3,Math.log((ta+.5)/(tb+.5))*.18));
const weight=Math.min(.8,Math.min(na,nb)/(Math.min(na,nb)+24)+(ea?.2:0));
const p=1/(1+Math.exp(-(strength+strike+td)*weight));
const record=n=>{const r=records.get(normalized(n));return r?r.wins+'-'+r.losses:'unmatched'};
const article=make('article');article.className='ksl-ufc-card';results.append(article);
article.append(make('h4',f.red+' vs '+f.blue+' · '+new Date(f.start_time).toLocaleString('en-US',{timeZone:'America/New_York',timeZoneName:'short'})));
article.append(make('p','1 · Career: UFC historical rounds '+na+' / '+nb+' · sampled W-L '+record(f.red)+' / '+record(f.blue)+' · pre-UFC record UNVERIFIED'));
article.append(make('p','2 · Opponent strength: '+(ea?'historical Elo available':'opponent-adjusted evidence UNAVAILABLE')));
article.append(make('p','3 · Sparse-data research prior: '+f.red+' '+pct(p)+' / '+f.blue+' '+pct(1-p)+(weight===0?' · NEUTRAL PRIOR, no fighter evidence':' · uncalibrated, uncertain')));
article.append(make('p','4 · Style and duration simulation: UNAVAILABLE · trained finish hazards and opponent-adjusted style inputs missing'));
article.append(make('p','5 · Odds/EV: RESEARCH ONLY · no calibrated model EV · '+(Date.now()-Date.parse(odds.fetched_at)<900000?'recent saved odds':'stale saved odds')));
}
state.textContent=total+' fights audited · '+missing+' lack paired UFC round histories · '+(baseline.pre_update_evaluated_fights||0)+' independently evaluated pre-update Elo forecasts · 0 model-verified bets.';
}catch(e){state.textContent='UNAVAILABLE — '+e.message}finally{refresh.disabled=false}
}
refresh.addEventListener('click',auditFights);auditFights();

}).catch(e=>{status.textContent='UNAVAILABLE — saved research datasets failed validation: '+e.message});
})();