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
}).catch(e=>{status.textContent='UNAVAILABLE — saved research datasets failed validation: '+e.message});
})();