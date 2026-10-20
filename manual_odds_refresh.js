// Manual odds refresh for mobile. Reads published, authorized feed snapshots only.
// Never calls a sportsbook directly or represents cached data as live.
(()=>{'use strict';
const $=id=>document.getElementById(id);
const css=document.createElement('style');css.textContent=`
#odds-refresh-panel{margin:16px 0;padding:14px;background:#101a17;border:1px solid #2a5744;border-radius:14px}
#odds-refresh-panel button{background:#25bd77;color:#06120d;border:0;border-radius:12px;padding:13px 18px;font-weight:800;min-height:48px;width:100%;cursor:pointer}
#odds-refresh-panel button:disabled{opacity:.65}
#odds-refresh-panel select{width:100%;min-height:44px;background:#101a17;color:#fff;border:1px solid #466356;border-radius:8px;margin:8px 0;padding:8px}
#odds-refresh-panel table{width:100%;font-size:12px;border-collapse:collapse}
#odds-refresh-panel th,#odds-refresh-panel td{padding:9px 5px;text-align:left;border-bottom:1px solid #2b3d34}
#odds-refresh-panel .scroll{overflow-x:auto}
#odds-refresh-panel .muted{color:#b5c4ba;font-size:12px;line-height:1.5}
`;document.head.append(css);
const panel=document.createElement('section');panel.id='odds-refresh-panel';
panel.innerHTML='<h2>Live Odds · Published Feed</h2><p class="muted">Manual refresh checks the most recently published authorized feed. It cannot collect new FanDuel or DraftKings prices by itself.</p><label for="odds-refresh-sport">Sport</label><select id="odds-refresh-sport"><option value="latest">Most recently updated</option><option value="americanfootball_nfl">NFL</option><option value="americanfootball_ncaaf">NCAA Football</option><option value="basketball_nba">NBA</option><option value="basketball_ncaab">NCAA Basketball</option><option value="baseball_mlb">MLB</option><option value="icehockey_nhl">NHL</option><option value="soccer_epl">Premier League</option></select><label for="odds-refresh-market">Market</label><select id="odds-refresh-market"><option value="all">All available</option><option value="h2h">Moneyline</option><option value="spreads">Spread</option><option value="totals">Total</option></select><label for="odds-refresh-book">Sportsbook</label><select id="odds-refresh-book"><option value="best">Best available</option><option value="fanduel">FanDuel</option><option value="draftkings">DraftKings</option></select><button id="odds-refresh-button" type="button">Refresh odds now</button><p class="muted" id="odds-refresh-status" role="status" aria-live="polite">No odds feed checked yet.</p><div class="scroll"><table><thead><tr><th>Event / Player</th><th>Market</th><th>Line</th><th>Book</th><th>Odds</th></tr></thead><tbody id="odds-refresh-results"></tbody></table></div>';
(document.querySelector('main')||document.body).prepend(panel);
const button=$('odds-refresh-button'),status=$('odds-refresh-status'),tbody=$('odds-refresh-results'),book=$('odds-refresh-book'),sport=$('odds-refresh-sport'),market=$('odds-refresh-market');
let snapshot=null;
const clean=v=>String(v??'—');
function render(){tbody.replaceChildren();if(!snapshot)return;
const rows=snapshot.odds.filter(x=>(market.value==='all'||x.market===market.value)&&(book.value==='best'||String(x.bookmaker||x.book||'').toLowerCase().includes(book.value)));
for(const x of rows){const tr=document.createElement('tr');for(const val of [x.event||x.player||x.description,x.market,x.point??x.line,x.bookmaker||x.book,x.price??x.odds]){const td=document.createElement('td');td.textContent=clean(val);tr.append(td)}tbody.append(tr)}
if(!rows.length)status.textContent+=' · No selections for '+book.options[book.selectedIndex].text;
}
book.addEventListener('change',render);market.addEventListener('change',render);
button.addEventListener('click',async()=>{button.disabled=true;button.textContent='Checking feed…';tbody.replaceChildren();snapshot=null;
try{const response=await fetch('./feed/'+(sport.value==='latest'?'latest':sport.value)+'.json?checked='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error('No published feed available');
const data=await response.json();if(!data||!Array.isArray(data.odds)||data.source!=='the-odds-api-v4')throw Error('Unrecognized feed format');
const time=Date.parse(data.fetched_at);const age=(Date.now()-time)/60000;const stale=!Number.isFinite(age)||age>15||age< -2;
snapshot=data;status.textContent=(stale?'STALE SNAPSHOT':'PUBLISHED SNAPSHOT')+' · Feed timestamp: '+clean(data.fetched_at)+' · '+clean(data.sport||'Unknown sport')+' · '+data.odds.length+' selections. Checked '+new Date().toLocaleTimeString()+'.';render();
}catch(err){status.textContent='UNAVAILABLE — '+err.message+'. No live sportsbook prices were retrieved.'}
finally{button.disabled=false;button.textContent='Refresh odds now';}});
})();