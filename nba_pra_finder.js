/* NBA PRA Finder — verified historical samples + live-market gating. */
(()=>{'use strict';
const root=document.getElementById('ksl-pra-finder');if(!root)return;
const $=(tag,txt)=>{const n=document.createElement(tag);if(txt!==undefined)n.textContent=txt;return n};
const style=$('style');style.textContent='.pra-controls{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.pra-controls select,.pra-controls button{background:#10283a;color:#fff;border:1px solid #42677b;border-radius:9px;padding:10px}.pra-card{background:#10283a;border:1px solid #42677b;border-radius:12px;padding:13px;margin:10px 0}.pra-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(95px,1fr));gap:7px;margin:10px 0}.pra-stat{background:#081426;border-radius:8px;padding:9px}.pra-stat strong{display:block;color:#f3c621}.pra-chart{display:flex;align-items:end;gap:3px;height:92px;margin:14px 0 4px}.pra-bar{flex:1;min-width:3px;background:#36c985;border-radius:3px 3px 0 0}.pra-bar.miss{background:#a65d5d}.pra-meta{color:#b8cbd8;font-size:13px}.pra-pass{color:#f3c621}';document.head.append(style);
const heading=$('h2','🏀 PRA Finder · Top 10');root.append(heading,$('p','Find the trend. Verify the edge. Bet the value. · P+R+A = Points + Rebounds + Assists'));
const controls=$('div');controls.className='pra-controls';const side=$('select');for(const v of ['Over','Under']){const o=$('option',v);o.value=v;side.append(o)}const refresh=$('button','Refresh PRA Finder');refresh.type='button';controls.append(side,refresh);root.append(controls);
const status=$('p','Loading verified player logs and sportsbook PRA lines…'),cards=$('div');status.setAttribute('role','status');root.append(status,cards);
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const aliases=[['points','pts'],['rebounds','reb'],['assists','ast']];
const num=(v,keys)=>{const k=Object.keys(v||{}).find(x=>keys.includes(norm(x)));if(!k||v[k]===null||v[k]==='')return null;const n=Number(v[k]);return Number.isFinite(n)&&n>=0?n:null};
const pra=g=>{const a=aliases.map(keys=>num(g.values,keys));return a.every(x=>x!==null)?a.reduce((s,x)=>s+x,0):null};
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const rate=(arr,line,over)=>arr.length?arr.filter(x=>over?x>line:x<line).length+'/'+arr.length:'—';
const pct=(arr,line,over)=>arr.length?Math.round(100*arr.filter(x=>over?x>line:x<line).length/arr.length)+'%':'—';
const implied=odds=>odds<0?-odds/(-odds+100):100/(odds+100);
const fmt=n=>Number.isFinite(n)?n.toFixed(1):'—';
const get=async f=>{const r=await fetch('./feed/'+f+'?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(f+' HTTP '+r.status);return r.json()};
let snapshot=null;
function draw(){cards.replaceChildren();if(!snapshot)return;const {stats,props,schedule}=snapshot,over=side.value==='Over',now=Date.now();
const events=(schedule.games||[]).filter(g=>Date.parse(g.commence_time)>now);
const quotes=(props.odds||[]).filter(q=>['draftkings','fanduel'].includes(String(q.bookmaker||'').toLowerCase())&&norm(q.market)==='playerpointsreboundsassists'&&String(q.outcome||q.name||'').toLowerCase()===side.value.toLowerCase()&&Number.isFinite(Number(q.point))&&Number.isFinite(Number(q.price))&&Date.parse(q.updated_at)<=now&&now-Date.parse(q.updated_at)<=900000&&Date.parse(q.commence_time)>now);
const byName=new Map();for(const q of quotes){const name=norm(q.player||q.player_name||q.description);if(!name)continue;const key=name+'|'+String(q.event_id);const prev=byName.get(key);if(!prev||implied(Number(q.price))<implied(Number(prev.price)))byName.set(key,q)}
const rows=[];for(const p of stats.players||[]){const logs=(p.games||[]).filter(g=>Number.isFinite(Date.parse(g.date))).sort((a,b)=>Date.parse(b.date)-Date.parse(a.date)).map(g=>({date:g.date,value:pra(g)})).filter(g=>g.value!==null);if(logs.length<5)continue;
for(const q of byName.values()){if(norm(q.player||q.player_name||q.description)!==norm(p.name))continue;if(!events.some(e=>String(e.event_id)===String(q.event_id)))continue;
const line=Number(q.point),history=logs.slice(0,20).map(g=>g.value),l5=history.slice(0,5),l10=history.slice(0,10),l20=history;
const trend=mean(l5)-mean(l10),projection=.55*mean(l5)+.30*mean(l10)+.15*mean(l20);
const hit=history.filter(x=>over?x>line:x<line).length, push=history.filter(x=>x===line).length;
const n=history.length,prob=(hit+1)/(n+2),breakEven=implied(Number(q.price)),edge=prob-breakEven;
const eligible=n>=10&&edge>=.05&&((over&&projection>line)||( !over&&projection<line))&&Math.abs(trend)>=.5;
rows.push({p,q,line,history,l5,l10,l20,trend,projection,prob,edge,breakEven,eligible,push})}}
rows.sort((a,b)=>Number(b.eligible)-Number(a.eligible)||b.edge-a.edge||b.history.length-a.history.length);
const top=rows.slice(0,10);status.textContent=top.length+' verified PRA markets · '+rows.filter(r=>r.eligible).length+' preliminary trend candidates · '+(stats.fetched_at||'unknown stats timestamp')+' · 15-minute maximum quote age · historical rates at today’s line (not historical closing-line hit rates)';
if(!top.length){cards.append($('p','UNAVAILABLE — No matched, fresh DK/FD PRA markets and player logs for upcoming games. No fabricated Top 10 or bets.'));return}
top.forEach((r,i)=>{const c=$('article');c.className='pra-card';const title=$('h3',(i+1)+'. '+r.p.name+' · '+(r.p.team||'NBA')+' · '+side.value+' '+r.line);c.append(title,$('p',r.q.bookmaker+' '+(Number(r.q.price)>0?'+':'')+r.q.price+' · '+(r.eligible?'TREND CANDIDATE — verify lineup, calibration and simulator before betting':'PASS — no verified betting edge')));
const grid=$('div');grid.className='pra-grid';for(const [label,value] of [['L5',rate(r.l5,r.line,over)+' · '+pct(r.l5,r.line,over)],['L10',rate(r.l10,r.line,over)+' · '+pct(r.l10,r.line,over)],['L20',rate(r.l20,r.line,over)+' · '+pct(r.l20,r.line,over)],['Projection',fmt(r.projection)],['Trend L5−L10',(r.trend>=0?'+':'')+fmt(r.trend)],['Smoothed hit %',Math.round(100*r.prob)+'%'],['Break-even',Math.round(100*r.breakEven)+'%'],['Raw edge',(r.edge>=0?'+':'')+(r.edge*100).toFixed(1)+' pp']]){const box=$('div');box.className='pra-stat';box.append($('small',label),$('strong',value));grid.append(box)}c.append(grid);
const chart=$('div');chart.className='pra-chart';chart.setAttribute('role','img');chart.setAttribute('aria-label','Last '+r.history.length+' PRA results oldest to newest against '+r.line);const max=Math.max(1,...r.history,r.line);for(const v of [...r.history].reverse()){const bar=$('div');bar.className='pra-bar'+((over?v<=r.line:v>=r.line)?' miss':'');bar.style.height=Math.max(3,100*v/max)+'%';bar.title=v+' PRA';chart.append(bar)}c.append(chart,$('p','Last '+r.history.length+' completed games · line '+r.line+' · '+r.push+' pushes · green = hit, red = miss/push'));
const meta=$('p','Historical trend screen only. Simulation and out-of-sample calibration not verified here; injury/lineup checks required.');meta.className='pra-meta';c.append(meta);cards.append(c)})}
async function load(){status.textContent='Refreshing PRA feeds…';try{const [stats,props,schedule]=await Promise.all([get('nba_player_stats.json'),get('nba_props.json'),get('nba_independent_game_inputs.json')]);if(!Array.isArray(stats.players)||!Array.isArray(props.odds)||!Array.isArray(schedule.games))throw Error('Feed schema invalid');snapshot={stats,props,schedule};draw()}catch(e){snapshot=null;cards.replaceChildren();status.textContent='UNAVAILABLE · '+e.message+' · Check existing NBA feed workflows';}}
side.addEventListener('change',draw);refresh.addEventListener('click',load);load();
})();