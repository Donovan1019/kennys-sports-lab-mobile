/* GameGrid-inspired detailed player controls. All displayed metrics derive from verified feeds. */
(()=>{'use strict';
const root=document.getElementById('ksl-player-page');if(!root)return;
const $=id=>document.getElementById(id);
const hero=root.querySelector('.ksl-p-hero'),controls=root.querySelector('.ksl-p-controls'),layout=root.querySelector('.ksl-p-layout'),chart=$('ksl-p-chart'),prices=$('ksl-p-prices');
const title=document.createElement('div');title.className='ks-pro-topline';title.innerHTML='<span>◈ KENNY’S SPORTS LAB</span><span>PLAYER INTELLIGENCE / VERIFIED DATA</span>';hero.prepend(title);
const stats=document.createElement('div');stats.id='ks-pro-stats';stats.className='ks-pro-stats';hero.append(stats);
const markets=['Receiving yards','Receptions','Rushing yards','Passing yards','Passing touchdowns','Rushing touchdowns','Receiving touchdowns'];
const tabs=document.createElement('div');tabs.className='ks-pro-market-tabs';tabs.setAttribute('role','group');tabs.setAttribute('aria-label','Player markets');controls.before(tabs);
for(const market of markets){const b=document.createElement('button');b.type='button';b.textContent=market;b.onclick=()=>{ $('ksl-p-market').value=market;$('ksl-p-market').dispatchEvent(new Event('change',{bubbles:true}));refresh()};tabs.append(b)}
const summary=$('ksl-p-summary');const chartCard=chart.parentElement;
const tools=document.createElement('div');tools.className='ks-pro-chart-tools';
tools.innerHTML='<span class="ks-pro-eyebrow">HISTORICAL PERFORMANCE</span><div class="ks-pro-line-control"><button type="button" id="ks-pro-minus" aria-label="Decrease threshold">−</button><strong id="ks-pro-line">Line</strong><button type="button" id="ks-pro-plus" aria-label="Increase threshold">+</button></div>';
chartCard.insertBefore(tools,chart);
const actions=document.createElement('div');actions.className='ks-pro-actions';actions.innerHTML='<button type="button" id="ks-pro-home">Home</button><button type="button" id="ks-pro-away">Away</button><button type="button" id="ks-pro-reset">All games</button>';chartCard.insertBefore(actions,chart);
const splitTabs=document.createElement('div');splitTabs.className='ks-pro-subtabs';splitTabs.innerHTML='<button type="button" data-mode="books">Books</button><button type="button" data-mode="splits">Splits</button><button type="button" data-mode="matchup">Matchup</button>';prices.before(splitTabs);
const note=document.createElement('p');note.className='ks-pro-disclosure';prices.after(note);
let statsFeed=null,propFeed=null,venue='all',view='books',loading=false;
const norm=x=>String(x||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'');
const formatPrice=p=>Number.isFinite(p)?(p>0?'+':'')+p:'—';
async function fetchFeeds(){if(statsFeed)return;const [a,b]=await Promise.all([fetch('./feed/nfl_player_stats.json'),fetch('./feed/nfl_props.json')]);if(!a.ok)throw Error('Verified player data unavailable');const d=await a.json();if(d.source!=='nflverse-stats-player-week'||!Array.isArray(d.players))throw Error('Player feed failed verification');statsFeed=d;if(b.ok){const p=await b.json();if(p.source==='the-odds-api-v4-event-props'&&Array.isArray(p.odds))propFeed=p}}
function cell(parent,tag,value,cls){const e=document.createElement(tag);e.textContent=value;if(cls)e.className=cls;parent.append(e);return e}
function getPlayer(){const q=norm($('ksl-p-find').value);return statsFeed?.players.find(p=>norm(p.name)===q)||statsFeed?.players.find(p=>q.length>=3&&norm(p.name).includes(q))}
function history(player,market){const season=$('ksl-p-season').value,win=$('ksl-p-window').value;let g=player.games.filter(x=>(season==='all'||String(x.season)===season)&&Number.isFinite(x.values?.[market]));if(venue!=='all')g=g.filter(x=>String(x.home_away||x.venue||'').toLowerCase()===venue);return win==='all'?g:g.slice(-Number(win))}
function render(){if(!statsFeed)return;const player=getPlayer();if(!player)return;const market=$('ksl-p-market').value,line=Number($('ksl-p-line').value);if(!Number.isFinite(line)||line<0)return;
for(const b of tabs.children)b.classList.toggle('selected',b.textContent===market);
for(const b of actions.children)b.classList.toggle('selected',b.id==='ks-pro-'+venue);
for(const b of splitTabs.children)b.classList.toggle('selected',b.dataset.mode===view);
$('ks-pro-line').textContent=market+' · '+line+'+';
const games=history(player,market),n=games.length,hits=games.filter(g=>g.values[market]>=line).length;
const average=n?games.reduce((a,g)=>a+g.values[market],0)/n:0;
$('ksl-p-hit').textContent=n?Math.round(100*hits/n)+'%':'—';
summary.textContent=n?'Cleared '+line+' in '+hits+' of '+n+' verified games · averaging '+average.toFixed(1):'No verified games for these filters';
$('ksl-p-name').textContent=player.name;$('ksl-p-team').textContent=(player.team||'Team unavailable')+' · NFL · '+$('ksl-p-season').value;
stats.replaceChildren();for(const m of markets){const values=history(player,m).map(g=>g.values[m]).filter(Number.isFinite),mean=values.length?values.reduce((a,v)=>a+v,0)/values.length:null;const tile=cell(stats,'div','', 'ks-pro-stat');cell(tile,'strong',mean===null?'—':mean.toFixed(1));cell(tile,'small',m+' · historical avg')}
chart.replaceChildren();const max=Math.max(line,1,...games.map(g=>g.values[market]));chart.style.setProperty('--ks-threshold-position',Math.min(100,100*line/max)+'%');for(const g of games){const bar=cell(chart,'div','', 'ksl-p-bar');cell(bar,'strong',String(g.values[market]));const fill=cell(bar,'div','',g.values[market]>=line?'':'fail');fill.style.height=Math.max(4,Math.round(165*g.values[market]/max))+'px';cell(bar,'small',String(g.season).slice(-2)+' W'+g.week)}
const splits=$('ksl-p-splits');splits.replaceChildren();for(const window of [3,5,10,20]){const season=$('ksl-p-season').value;const all=player.games.filter(g=>(season==='all'||String(g.season)===season)&&Number.isFinite(g.values?.[market]));const subset=all.slice(-window),h=subset.filter(g=>g.values[market]>=line).length;cell(splits,'span','L'+window+' '+(subset.length?Math.round(100*h/subset.length)+'%':'—')+' ('+h+'/'+subset.length+')')}
prices.replaceChildren();
if(view==='matchup'){cell(prices,'p','Opponent-specific defensive matchups and projected next-game performance: UNAVAILABLE. Verified defensive and schedule feeds are not connected.','ks-pro-disclosure')}
else if(view==='splits'){const all=player.games.filter(g=>Number.isFinite(g.values?.[market]));const bySeason=[...new Set(all.map(g=>g.season))].sort((a,b)=>b-a);for(const yr of bySeason){const subset=all.filter(g=>g.season===yr),h=subset.filter(g=>g.values[market]>=line).length;cell(prices,'div',yr+': '+h+'/'+subset.length+' hits · '+(100*h/subset.length).toFixed(0)+'%','ksl-p-price')}cell(prices,'p','Home/away filters require verified venue fields. This feed does not provide them.','ks-pro-disclosure')}
else {const map={'Receiving yards':'player_reception_yds','Receptions':'player_receptions','Rushing yards':'player_rush_yds','Passing yards':'player_pass_yds','Passing touchdowns':'player_pass_tds'};const rows=(propFeed?.odds||[]).filter(x=>norm(x.player)===norm(player.name)&&x.market===map[market]);if(!rows.length)cell(prices,'p','No saved sportsbook prices for this player and market.','ks-pro-disclosure');else {const table=cell(prices,'table','','ks-pro-price-table'),thead=cell(table,'thead',''),tr=cell(thead,'tr','');for(const label of ['BOOK','LINE','OVER','UNDER'])cell(tr,'th',label);const body=cell(table,'tbody','');const grouped=new Map();for(const r of rows){const key=r.bookmaker+'|'+r.point;if(!grouped.has(key))grouped.set(key,{book:r.bookmaker,point:r.point});grouped.get(key)[String(r.selection).toLowerCase()]=r.price}for(const r of grouped.values()){const tr=cell(body,'tr','');for(const value of [r.book,r.point,formatPrice(r.over),formatPrice(r.under)])cell(tr,'td',String(value))}}}
note.textContent='Historical hit rates and averages are not next-game projections. Odds snapshot: '+(propFeed?.fetched_at||'unavailable')+'. No model probability until validated.';
$('ksl-p-status').textContent='Verified player history: '+(statsFeed.fetched_at||'date unavailable')+' · '+n+' games displayed.'}
async function refresh(){if(loading)return;loading=true;try{await fetchFeeds();render()}catch(e){$('ksl-p-status').textContent='UNAVAILABLE: '+e.message}finally{loading=false}}
$('ks-pro-minus').onclick=()=>{const input=$('ksl-p-line');input.value=Math.max(0,Number(input.value)-(Number(input.step)||.5));input.dispatchEvent(new Event('change'));render()};
$('ks-pro-plus').onclick=()=>{const input=$('ksl-p-line');input.value=Number(input.value)+(Number(input.step)||.5);input.dispatchEvent(new Event('change'));render()};
for(const b of actions.children)b.onclick=()=>{venue=b.id.replace('ks-pro-','');if(venue!=='all'){venue='all';$('ksl-p-status').textContent='Home/away game labels are not present in the verified feed; showing all games.'}render()};
for(const b of splitTabs.children)b.onclick=()=>{view=b.dataset.mode;render()};
for(const id of ['ksl-p-find','ksl-p-market','ksl-p-line','ksl-p-season','ksl-p-window'])$(id).addEventListener('change',()=>{venue='all';refresh()});
$('ksl-p-load').addEventListener('click',()=>setTimeout(refresh,0));
})();