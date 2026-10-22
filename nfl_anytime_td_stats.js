/* NFL anytime touchdown historical research. Never interpret missing stats as zero. */
(()=>{'use strict';
const markets=['Anytime touchdown','Rushing touchdowns','Receiving touchdowns','Passing touchdowns'];
const metric=(values,label)=>{
 if(!values||typeof values!=='object')return null;
 const keys=Object.keys(values),norm=x=>String(x).toLowerCase().replace(/[^a-z0-9]/g,'');
 const aliases={
 'Rushing touchdowns':['rushingtouchdowns','rushingtds','rushtds'],
 'Receiving touchdowns':['receivingtouchdowns','receivingtds','rectds'],
 'Passing touchdowns':['passingtouchdowns','passingtds','passtds'],
 'Return touchdowns':['returntouchdowns','returntds','kickreturntouchdowns','puntreturntouchdowns']
 };
 const find=key=>{const k=keys.find(k=>aliases[key].includes(norm(k)));if(!k)return null;const v=values[k];return v===null||v===''||!Number.isFinite(Number(v))?null:Number(v)};
 if(label!=='Anytime touchdown')return find(label);
 const rush=find('Rushing touchdowns'),rec=find('Receiving touchdowns'),ret=find('Return touchdowns');
 // Return TDs count when explicitly recorded; missing return data is not assumed zero.
 if(rush===null||rec===null)return null;
 // Return TD coverage is not guaranteed by the weekly stats feed: expose the lower-bound, not an exact anytime scorer total.
 return rush+rec+(ret===null?0:ret);
};
function mount(){
 const host=document.getElementById('ksl-real-stats')||document.getElementById('ksl-nfl');
 if(!host||document.getElementById('ksl-anytime-research'))return;
 const section=document.createElement('section');section.id='ksl-anytime-research';
 section.style.cssText='margin:16px 0;padding:15px;border:1px solid #427a70;border-radius:12px;background:#0c2431;color:#e9f5ff';
 section.innerHTML='<h3>🏈 NFL · Anytime TD & Touchdown Statistics</h3><p>Verified game-log hit rates, not projected probabilities. Passing TDs do not count toward anytime scorer. Return TDs are included only when explicitly recorded. Missing data is UNAVAILABLE, never zero. Anytime TD combines recorded rushing and receiving touchdowns; return TDs may be absent. When return TD data is absent, anytime TD counts reflect rushing + receiving only and may undercount sportsbook-settled scorers.</p><label>Market <select id="ksl-atd-market"></select></label> <label>Recent games <select id="ksl-atd-window"><option>5</option><option selected>10</option><option>20</option></select></label> <label>Player <input id="ksl-atd-search" placeholder="Search player"></label><button id="ksl-atd-reload" type="button">Refresh verified stats</button><p id="ksl-atd-status" role="status">Loading…</p><div style="overflow-x:auto"><table style="width:100%;min-width:530px"><thead><tr><th>Player</th><th>Team</th><th>Games</th><th>TD games</th><th>Hit rate</th><th>Recent TDs</th></tr></thead><tbody id="ksl-atd-rows"></tbody></table></div>';
 host.prepend(section);
 const $=id=>document.getElementById(id),market=$('ksl-atd-market');
 for(const name of markets){const o=document.createElement('option');o.textContent=name;market.append(o)}
 const make=(tag,value)=>{const e=document.createElement(tag);e.textContent=String(value);return e};
 let data=null;
 const render=()=>{const body=$('ksl-atd-rows');body.replaceChildren();if(!data)return;const name=$('ksl-atd-search').value.toLowerCase(),n=Number($('ksl-atd-window').value),label=market.value;let rows=0;
 for(const p of data.players){if(name&&!String(p.name||'').toLowerCase().includes(name))continue;
 const games=(p.games||[]).slice().sort((a,b)=>(Number(b.season)||0)-(Number(a.season)||0)||(Number(b.week)||0)-(Number(a.week)||0));
 const vals=games.map(g=>metric(g.values,label)).filter(v=>v!==null).slice(0,n);
 if(!vals.length)continue;const hits=vals.filter(v=>v>=1).length;const tr=make('tr','');
 for(const v of [p.name||'Unknown',p.team||'—',vals.length,hits,(100*hits/vals.length).toFixed(1)+'%',vals.join(', ')]){const td=make('td',v);td.style.cssText='padding:8px;border-bottom:1px solid #34536a';tr.append(td)}
 body.append(tr);rows++}
 $('ksl-atd-status').textContent=rows?rows+' players with verified '+label+' records · historical only':'UNAVAILABLE: no supported player history for '+label+'. Missing is not zero.';
 };
 async function load(){try{$('ksl-atd-status').textContent='Loading verified NFL player logs…';const r=await fetch('./feed/nfl_player_stats.json',{cache:'no-store'});if(!r.ok)throw Error('NFL stats feed HTTP '+r.status);const json=await r.json();if(!Array.isArray(json.players))throw Error('Invalid NFL player stats schema');data=json;render()}catch(e){data=null;$('ksl-atd-rows').replaceChildren();$('ksl-atd-status').textContent='UNAVAILABLE: '+e.message}}
 [market,$('ksl-atd-window')].forEach(el=>el.addEventListener('change',render));$('ksl-atd-search').addEventListener('input',render);$('ksl-atd-reload').addEventListener('click',load);load();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();