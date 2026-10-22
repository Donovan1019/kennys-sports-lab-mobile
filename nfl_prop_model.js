/* Exploratory NFL player prop model.
 * Verified game logs + verified published odds, with explicit small-sample shrinkage.
 * This is not a validated or calibrated betting model. No injury/role adjustment.
 */
(()=>{'use strict';
const marketMap={'player_pass_yds':'Passing yards','player_pass_tds':'Passing touchdowns','player_rush_yds':'Rushing yards','player_reception_yds':'Receiving yards','player_receptions':'Receptions','player_anytime_td':'Anytime touchdown'};
const panel=document.createElement('section');panel.id='ksl-model';
panel.innerHTML='<h2>NFL Prop Model · Experimental</h2><p class="ksl-model-note">Joins real player logs to published FanDuel/DraftKings prop lines. Simulates 10,000 outcomes by resampling recorded player games. Estimates are exploratory, NOT calibrated probabilities or betting recommendations. No injury, matchup, weather or projected workload adjustment.</p><label>2026 player games (minimum 5) <input id="ksl-model-min" type="number" min="5" max="20" value="5"></label><button id="ksl-model-run" type="button">Run 10,000-sample prop analysis</button><p id="ksl-model-status" role="status" class="ksl-model-note">Requires published NFL props and verified game logs.</p><div class="ksl-model-scroll"><table><thead><tr><th>Player</th><th>Market</th><th>Line</th><th>Book / odds</th><th>2026 games</th><th>Historical over</th><th>Bootstrap over</th><th>Break-even</th><th>Notes</th></tr></thead><tbody id="ksl-model-rows"></tbody></table></div>';
const style=document.createElement('style');style.textContent='#ksl-model{background:#101a17;border:1px solid #2a5744;border-radius:14px;padding:16px;margin:18px 0}#ksl-model h2{color:#70ef91}#ksl-model .ksl-model-note{font-size:13px;color:#b4c6bb;line-height:1.5}#ksl-model button{min-height:46px;background:#25bd77;color:#06120d;border:0;border-radius:9px;padding:10px;font-weight:800}#ksl-model input{max-width:80px;min-height:42px}#ksl-model .ksl-model-scroll{overflow:auto;max-height:650px}#ksl-model table{min-width:950px;border-collapse:collapse;font-size:12px}#ksl-model td,#ksl-model th{padding:9px;border-bottom:1px solid #2a4134;text-align:left}';document.head.append(style);(document.querySelector('main')||document.body).prepend(panel);
const $=id=>document.getElementById(id);
const normalize=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'');
const implied=p=>p<0?-p/(-p+100):100/(p+100);
const american=p=>(p>0?'+':'')+p;
function sample(values,line,trials=10000){let hits=0;for(let i=0;i<trials;i++){const v=values[Math.floor(Math.random()*values.length)];if(v>line)hits++}return hits/trials}
$('ksl-model-run').onclick=async()=>{
 const status=$('ksl-model-status'),body=$('ksl-model-rows');body.replaceChildren();
 const min=Number($('ksl-model-min').value);if(!Number.isInteger(min)||min<5||min>20){status.textContent='Choose 5–20 minimum games.';return}
 status.textContent='Loading verified saved feeds…';
 try{
  const [statsResponse,propsResponse]=await Promise.all(['./feed/nfl_player_stats.json','./feed/nfl_props.json'].map(p=>fetch(p+'?t='+Date.now(),{cache:'no-store'})));
  if(!statsResponse.ok||!propsResponse.ok)throw Error('Missing verified stats or prop feed');
  const [stats,props]=await Promise.all([statsResponse.json(),propsResponse.json()]);
  if(stats.source!=='nflverse-stats-player-week'||props.source!=='the-odds-api-v4-event-props'||!Array.isArray(stats.players)||!Array.isArray(props.odds))throw Error('Feed provenance mismatch');
  const byName=new Map();for(const player of stats.players){const key=normalize(player.name);if(key&&!byName.has(key))byName.set(key,player)}
  const groups=new Map();for(const r of props.odds){
   if(!marketMap[r.market]||r.selection!=='Over'||!Number.isFinite(r.point)||!Number.isFinite(r.price)||!(r.price<=-100||r.price>=100))continue;
   const key=JSON.stringify([r.event_id,normalize(r.player),r.market,r.point]);const old=groups.get(key);
   if(!old||implied(r.price)<implied(old.price))groups.set(key,r);
  }
  const records=[];let unmatched=0,short=0;
  for(const r of groups.values()){
   const player=byName.get(normalize(r.player));if(!player){unmatched++;continue}
   const metric=marketMap[r.market];const games=player.games.filter(g=>String(g.season)==='2026'&&Number.isFinite(g.values?.[metric])).slice(-20);
   if(games.length<min){short++;continue}
   const values=games.map(g=>g.values[metric]);const hit=values.filter(v=>v>r.point).length;
   const bootstrap=sample(values,r.point);
   records.push({r,player,n:games.length,hit,bootstrap,breakeven:implied(r.price)});
  }
  records.sort((a,b)=>b.n-a.n||a.player.name.localeCompare(b.player.name));
  for(const x of records.slice(0,150)){
   const tr=document.createElement('tr');for(const value of [x.player.name,marketMap[x.r.market],x.r.point,x.r.bookmaker+' '+american(x.r.price),x.n,x.hit+'/'+x.n+' ('+(100*x.hit/x.n).toFixed(0)+'%)',(100*x.bootstrap).toFixed(1)+'%',(100*x.breakeven).toFixed(1)+'%','Exploratory only; not calibrated']){
    const td=document.createElement('td');td.textContent=String(value);tr.append(td)
   }body.append(tr)
  }
  const age=(Date.now()-Date.parse(props.fetched_at))/60000;
  status.textContent=records.length+' qualifying lines · '+unmatched+' unmatched player names · '+short+' below minimum games · props fetched '+props.fetched_at+(age>15?' (STALE)':'')+'. Bootstrap reproduces empirical rates within sampling noise; it does not create independent predictive evidence. EV intentionally withheld until out-of-sample calibration.';
 }catch(e){status.textContent='UNAVAILABLE: '+e.message}
};
})();