/* NBA PRA Finder — verified historical samples + live-market gating. */
(()=>{'use strict';
const root=document.getElementById('ksl-pra-finder');if(!root)return;
const $=(tag,txt)=>{const n=document.createElement(tag);if(txt!==undefined)n.textContent=txt;return n};
const style=$('style');style.textContent='.pra-controls{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.pra-controls select,.pra-controls button{background:#10283a;color:#fff;border:1px solid #42677b;border-radius:9px;padding:10px}.pra-card{background:#10283a;border:1px solid #42677b;border-radius:12px;padding:13px;margin:10px 0}.pra-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(95px,1fr));gap:7px;margin:10px 0}.pra-stat{background:#081426;border-radius:8px;padding:9px}.pra-stat strong{display:block;color:#f3c621}.pra-chart{display:flex;align-items:end;gap:3px;height:92px;margin:14px 0 4px}.pra-bar{flex:1;min-width:3px;background:#36c985;border-radius:3px 3px 0 0}.pra-bar.miss{background:#a65d5d}.pra-meta{color:#b8cbd8;font-size:13px}.pra-pass{color:#f3c621} #ksl-pra-finder{--pra-bg:#0b0b0d;--pra-panel:#191a1d;--pra-edge:#303135;--pra-yellow:#f3c621;--pra-green:#18b75c;--pra-red:#e5474c;color:#f5f5f5} #ksl-pra-finder .pra-card{background:var(--pra-panel);border-color:var(--pra-edge)} #ksl-pra-finder .pra-stat{background:#101113} #ksl-pra-finder .pra-stat strong{color:var(--pra-yellow)} #ksl-pra-finder .pra-controls button[aria-pressed="true"]{border-color:var(--pra-yellow);color:var(--pra-yellow)} .pra-viz{display:grid;grid-template-columns:minmax(0,2fr) minmax(190px,1fr);gap:12px;margin:16px 0} .pra-viz-panel{background:#111214;border:1px solid #323438;border-radius:12px;padding:12px;min-width:0} .pra-viz-panel h4{margin:0 0 10px;color:#f3c621;font-size:14px} .pra-svg{width:100%;height:auto;display:block;overflow:visible} .pra-svg .pra-hit{fill:#18b75c}.pra-svg .pra-miss{fill:#e5474c}.pra-svg .pra-push{fill:#f3c621} .pra-svg .pra-target{stroke:#f3c621;stroke-width:2;stroke-dasharray:5 4} .pra-svg .pra-label{fill:#adb0b7;font-size:10px} .pra-svg .pra-point{fill:#f3c621;stroke:#101113;stroke-width:2} .pra-svg .pra-trend{fill:none;stroke:#f3c621;stroke-width:2.5} .pra-svg .pra-bar-click{cursor:pointer;outline:none} .pra-svg .pra-bar-click:focus-visible{stroke:#fff;stroke-width:2} .pra-pie-wrap{display:flex;gap:16px;align-items:center;justify-content:center;flex-wrap:wrap} .pra-donut{width:138px;height:138px;border-radius:50%;display:grid;place-items:center;flex:none} .pra-donut-inner{width:95px;height:95px;border-radius:50%;background:#111214;display:flex;flex-direction:column;justify-content:center;align-items:center} .pra-donut-inner strong{font-size:25px;color:#f3c621} .pra-legend{font-size:12px;line-height:1.9} .pra-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px} .pra-chart-buttons{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0} .pra-chart-buttons button{padding:7px 11px!important;font-size:12px!important} .pra-chart-buttons button[aria-pressed="true"]{border-color:#f3c621!important;color:#f3c621!important} .pra-detail{margin:8px 0;color:#d9e1e6;font-size:13px;min-height:20px} @media(max-width:640px){.pra-viz{grid-template-columns:1fr}.pra-viz-panel{padding:9px}.pra-donut{width:120px;height:120px}.pra-donut-inner{width:84px;height:84px}} ';document.head.append(style);
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
function bootstrap(history,line,over,seed){let state=seed>>>0;const random=()=>{state=(1664525*state+1013904223)>>>0;return state/4294967296};const samples=[];let hits=0;for(let i=0;i<10000;i++){const value=history[Math.floor(random()*history.length)];samples.push(value);if(over?value>line:value<line)hits++}samples.sort((a,b)=>a-b);return {prob:hits/10000,low:samples[1000],high:samples[8999]}}

const get=async f=>{const r=await fetch('./feed/'+f+'?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(f+' HTTP '+r.status);return r.json()};

function makeViz(r){
const holder=$('div');const actions=$('div');actions.className='pra-chart-buttons';const viz=$('div');viz.className='pra-viz';holder.append(actions,viz);
let windowSize=20,mode='Bars',selected=-1;
const makeButton=(label,pressed,onClick)=>{const b=$('button',label);b.type='button';b.setAttribute('aria-pressed',String(pressed));b.addEventListener('click',onClick);actions.append(b);return b};
const svgEl=(tag,attrs={})=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));return n};
const render=()=>{
actions.replaceChildren();viz.replaceChildren();
for(const n of [5,10,20])makeButton('L'+n,windowSize===n,()=>{windowSize=n;selected=-1;render()});
for(const m of ['Bars','Trend'])makeButton(m,mode===m,()=>{mode=m;selected=-1;render()});
const values=r.history.slice(0,windowSize).reverse(),dates=(r.dates||[]).slice(0,windowSize).reverse(),over=side.value==='Over';
const left=$('div');left.className='pra-viz-panel';left.append($('h4',mode==='Bars'?'Game-by-game PRA vs sportsbook line':'PRA trend · 3-game rolling average'));
const graph=svgEl('svg',{viewBox:'0 0 500 220',class:'pra-svg',role:'group','aria-label':mode+' chart, last '+values.length+' games; select a game for details'});
const max=Math.max(1,r.line,...values)*1.16,base=183,top=16,usable=base-top,y=v=>base-v/max*usable;
for(const v of [0,Math.round(max/2),Math.round(max)]){const yy=y(v);graph.append(svgEl('line',{x1:38,x2:488,y1:yy,y2:yy,stroke:'#323438','stroke-width':1}));const t=svgEl('text',{x:32,y:yy+4,'text-anchor':'end',class:'pra-label'});t.textContent=v;graph.append(t)}
graph.append(svgEl('line',{x1:38,x2:488,y1:y(r.line),y2:y(r.line),class:'pra-target'}));
const target=svgEl('text',{x:486,y:y(r.line)-5,'text-anchor':'end',fill:'#f3c621','font-size':11});target.textContent='Line '+r.line;graph.append(target);
const width=450/Math.max(1,values.length);
if(mode==='Bars'){values.forEach((v,i)=>{const x=38+i*width+width*.12,hit=over?v>r.line:v<r.line,push=v===r.line;
const rect=svgEl('rect',{x,y:y(v),width:Math.max(3,width*.76),height:Math.max(1,base-y(v)),rx:2,class:'pra-bar-click '+(push?'pra-push':hit?'pra-hit':'pra-miss'),tabindex:0,role:'button','aria-label':'Game '+(i+1)+': '+v+' PRA, '+(hit?'hit':push?'push':'miss')});
const select=()=>{selected=i;detail.textContent=(dates[i]||'Game '+(i+1))+' · '+v+' P+R+A · '+(hit?'HIT':push?'PUSH':'MISS')+' vs '+r.line};rect.addEventListener('click',select);rect.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select()}});const tt=svgEl('title');tt.textContent=(dates[i]||'Game')+' · '+v+' PRA';rect.append(tt);graph.append(rect)})}
else{const avg=values.map((_,i)=>{const s=values.slice(Math.max(0,i-2),i+1);return mean(s)});const points=avg.map((v,i)=>(38+(i+.5)*width)+','+y(v)).join(' ');graph.append(svgEl('polyline',{points,class:'pra-trend'}));avg.forEach((v,i)=>{const p=svgEl('circle',{cx:38+(i+.5)*width,cy:y(v),r:4,class:'pra-point pra-bar-click',tabindex:0,role:'button','aria-label':'Rolling average '+fmt(v)});const select=()=>{detail.textContent=(dates[i]||'Game '+(i+1))+' · 3-game average '+fmt(v)+' PRA'};p.addEventListener('click',select);p.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select()}});graph.append(p)})}
for(let i=0;i<values.length;i++){if(i%Math.max(1,Math.ceil(values.length/8))!==0)continue;const t=svgEl('text',{x:38+(i+.5)*width,y:203,'text-anchor':'middle',class:'pra-label'});t.textContent=dates[i]?String(dates[i]).slice(5):String(i+1);graph.append(t)}
left.append(graph);const detail=$('p','Tap a bar or point to inspect a game.');detail.className='pra-detail';left.append(detail);
const right=$('div');right.className='pra-viz-panel';right.append($('h4','Hit-rate breakdown · L'+values.length));
const hits=values.filter(v=>over?v>r.line:v<r.line).length,pushes=values.filter(v=>v===r.line).length,misses=values.length-hits-pushes;
const pie=$('div');pie.className='pra-pie-wrap';const donut=$('div');donut.className='pra-donut';const h=hits/values.length*100,p=pushes/values.length*100;
donut.style.background='conic-gradient(#18b75c 0% '+h+'%,#f3c621 '+h+'% '+(h+p)+'%,#e5474c '+(h+p)+'% 100%)';
const inner=$('div');inner.className='pra-donut-inner';inner.append($('strong',Math.round(h)+'%'),$('small','HIT RATE'));donut.append(inner);pie.append(donut);
const legend=$('div');legend.className='pra-legend';for(const [color,label,count] of [['#18b75c','Hits',hits],['#e5474c','Misses',misses],['#f3c621','Pushes',pushes]]){const line=$('div');const dot=$('span');dot.className='pra-dot';dot.style.background=color;line.append(dot,document.createTextNode(label+' · '+count));legend.append(line)}pie.append(legend);right.append(pie,$('p','Hit rate uses the currently selected sportsbook line, not past closing lines.'));viz.append(left,right);
};render();return holder;
}

function american(decimal){const n=decimal>=2?Math.round((decimal-1)*100):Math.round(-100/(decimal-1));return (n>0?'+':'')+n}
function parlayPanel(rows){
const panel=$('section');panel.className='pra-card';panel.append($('h3','PRA Parlay Builder · Historical Screen'));
const controls=$('div');controls.className='pra-controls';
const legs=$('select');for(const n of [2,3,4]){const option=$('option',n+' legs');option.value=n;legs.append(option)}
const book=$('select');for(const name of ['Best available','DraftKings','FanDuel']){const option=$('option',name);option.value=name;book.append(option)}
controls.append(legs,book);panel.append(controls);
const result=$('div');panel.append(result);
const render=()=>{
result.replaceChildren();const count=Number(legs.value),selectedBook=book.value.toLowerCase();
const available=rows.filter(r=>r.history.length>=10&&r.eligible&&(selectedBook==='best available'||r.q.bookmaker===selectedBook));
const picks=[],usedPlayers=new Set(),usedGames=new Set();
for(const r of available){const player=norm(r.p.name),event=String(r.q.event_id);if(usedPlayers.has(player)||usedGames.has(event))continue;picks.push(r);usedPlayers.add(player);usedGames.add(event);if(picks.length===count)break}
if(picks.length<count){result.append($('p','UNAVAILABLE — Only '+picks.length+' qualifying selections across distinct games with current '+side.value+' PRA quotes. No fabricated parlay.'));return}
let decimal=1,independent=1;const list=$('ol');
for(const r of picks){const price=Number(r.q.price);decimal*=price>0?1+price/100:1+100/Math.abs(price);independent*=r.sim.prob;
const item=$('li',r.p.name+' · '+side.value+' '+r.line+' PRA · '+r.q.bookmaker.toUpperCase()+' '+(price>0?'+':'')+price+' · L10 '+pct(r.l10,r.line,side.value==='Over')+' · L20 '+pct(r.l20,r.line,side.value==='Over'));list.append(item)}
result.append(list);
const joint=Math.pow(independent,1),breakeven=1/decimal;
result.append($('p','Illustrative combined price: '+american(decimal)+' · Decimal '+decimal.toFixed(2)+' · Independent historical-resampling estimate: '+(joint*100).toFixed(1)+'% · Break-even: '+(breakeven*100).toFixed(1)+'%'));
const sameBook=new Set(picks.map(r=>r.q.bookmaker)).size===1;
const caution=$('p',(sameBook?'Single-book quote set. ':'Mixed-book quote set: combined price may not be offered at any sportsbook. ')+'Distinct-game selections reduce same-game overlap, but results may still be correlated. Estimated probability is NOT calibrated, injury-adjusted or verified positive EV. Recheck all lines, availability and sportsbook parlay acceptance before betting. Recommendation: RESEARCH ONLY / PASS pending full simulation validation.');
caution.className='pra-meta';result.append(caution);
};legs.addEventListener('change',render);book.addEventListener('change',render);render();return panel
}

let snapshot=null;
function draw(){cards.replaceChildren();if(!snapshot)return;const {stats,props}=snapshot,over=side.value==='Over',now=Date.now();
const events=(props.odds||[]).filter(q=>Date.parse(q.commence_time)>now&&q.event_id).map(q=>String(q.event_id));const activeEvents=new Set(events);
const quotes=(props.odds||[]).filter(q=>['draftkings','fanduel'].includes(String(q.bookmaker||'').toLowerCase())&&norm(q.market)==='playerpointsreboundsassists'&&String(q.selection||q.outcome||q.name||'').toLowerCase()===side.value.toLowerCase()&&Number.isFinite(Number(q.point))&&Number.isFinite(Number(q.price))&&Date.parse(q.updated_at)<=now&&now-Date.parse(q.updated_at)<=3600000&&Date.parse(q.commence_time)>now);
const byName=new Map();for(const q of quotes){const name=norm(q.player||q.player_name||q.description);if(!name)continue;const key=name+'|'+String(q.event_id);const prev=byName.get(key);if(!prev||implied(Number(q.price))<implied(Number(prev.price)))byName.set(key,q)}
const rows=[];let qualifiedLogs=0,nameMatches=0;for(const p of stats.players||[]){const logs=(p.games||[]).filter(g=>Number.isFinite(Date.parse(g.date))&&Date.parse(g.date)>=Date.parse('2026-10-01')&&Date.parse(g.date)<now).sort((a,b)=>Date.parse(b.date)-Date.parse(a.date)).map(g=>({date:g.date,value:pra(g)})).filter(g=>g.value!==null);if(logs.length<5)continue;qualifiedLogs++;
for(const q of byName.values()){if(norm(q.player||q.player_name||q.description)!==norm(p.name))continue;nameMatches++;if(!activeEvents.has(String(q.event_id)))continue;
const line=Number(q.point),history=logs.slice(0,20).map(g=>g.value),l5=history.slice(0,5),l10=history.slice(0,10),l20=history;
const trend=mean(l5)-mean(l10),projection=.55*mean(l5)+.30*mean(l10)+.15*mean(l20);
const hit=history.filter(x=>over?x>line:x<line).length, push=history.filter(x=>x===line).length;
const n=history.length,prob=(hit+1)/(n+2),breakEven=implied(Number(q.price)),edge=prob-breakEven;
const eligible=n>=10&&edge>=.05&&((over&&projection>line)||(!over&&projection<line))&&Math.abs(trend)>=.5;
const sim=bootstrap(history,line,over,Number(q.event_id?.slice(0,7).replace(/[^0-9a-f]/gi,'')||'1',16)||1);rows.push({p,q,line,history,dates:logs.slice(0,20).map(g=>g.date),l5,l10,l20,trend,projection,prob,edge,breakEven,eligible,push,sim})}}
rows.sort((a,b)=>Number(b.eligible)-Number(a.eligible)||b.edge-a.edge||b.history.length-a.history.length);
const top=rows.slice(0,10);const newest=props.fetched_at||'unknown',stale=Date.parse(newest);status.textContent=top.length+' matched current PRA markets · '+rows.filter(r=>r.eligible).length+' historical trend candidates · odds feed '+newest+' · stats feed '+(stats.fetched_at||'unknown')+' · current season only · 60-minute quote limit';if(!top.length){const diagnostic=$('p','DATA STATUS · '+(props.odds||[]).filter(q=>norm(q.market)==='playerpointsreboundsassists').length+' PRA quotes in saved feed · '+(stats.players||[]).length+' player histories · '+qualifiedLogs+' with 5+ current-season games · '+quotes.length+' fresh '+side.value+' quotes · '+nameMatches+' player-name matches · '+activeEvents.size+' future sportsbook events. '+(Number.isFinite(stale)&&now-stale>3600000?'Odds feed is stale; refresh the existing sportsbook feed workflow.':'Check current event IDs, quote timestamps and player game logs.'));diagnostic.className='pra-meta';cards.append(diagnostic)}
if(!top.length){cards.append($('p','UNAVAILABLE — No matched, fresh DK/FD PRA markets and 2026–27 player logs for upcoming games. No fabricated Top 10 or bets.'));return}
cards.append(parlayPanel(rows));
top.forEach((r,i)=>{const c=$('article');c.className='pra-card';const title=$('h3',(i+1)+'. '+r.p.name+' · '+(r.p.team||'NBA')+' · '+side.value+' '+r.line);c.append(title,$('p',r.q.bookmaker+' '+(Number(r.q.price)>0?'+':'')+r.q.price+' · '+(r.eligible?'TREND CANDIDATE — verify lineup, calibration and simulator before betting':'PASS — no verified betting edge')));
const grid=$('div');grid.className='pra-grid';for(const [label,value] of [['L5',rate(r.l5,r.line,over)+' · '+pct(r.l5,r.line,over)],['L10',rate(r.l10,r.line,over)+' · '+pct(r.l10,r.line,over)],['L20',rate(r.l20,r.line,over)+' · '+pct(r.l20,r.line,over)],['Projection',fmt(r.projection)],['Trend L5−L10',(r.trend>=0?'+':'')+fmt(r.trend)],['Smoothed hit %',Math.round(100*r.prob)+'%'],['Break-even',Math.round(100*r.breakEven)+'%'],['Historical proxy edge',(r.edge>=0?'+':'')+(r.edge*100).toFixed(1)+' pp'],['Bootstrap MC hit',Math.round(r.sim.prob*100)+'%'],['MC 80% range',fmt(r.sim.low)+'–'+fmt(r.sim.high)]]){const box=$('div');box.className='pra-stat';box.append($('small',label),$('strong',value));grid.append(box)}c.append(grid);
c.append(makeViz(r));
const meta=$('p','Historical screen + 10,000-draw empirical Monte Carlo (historical resampling). This is NOT an injury-adjusted or out-of-sample calibrated betting probability. Recommendation: PASS pending verified availability, simulation calibration and exact live line.');meta.className='pra-meta';c.append(meta);cards.append(c)})}
async function load(){status.textContent='Refreshing PRA feeds…';try{const [stats,props]=await Promise.all([get('nba_player_stats.json'),get('nba_props.json')]);if(!Array.isArray(stats.players)||!Array.isArray(props.odds))throw Error('Feed schema invalid');snapshot={stats,props};draw()}catch(e){snapshot=null;cards.replaceChildren();status.textContent='UNAVAILABLE · '+e.message+' · Check existing NBA feed workflows';}}
side.addEventListener('change',draw);refresh.addEventListener('click',load);load();
})();