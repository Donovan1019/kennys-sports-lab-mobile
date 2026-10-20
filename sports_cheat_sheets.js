/* Cross-sport cheat sheets. Observed results and saved sportsbook prices are never conflated. */
(()=>{'use strict';
const defs=[
{sport:'NFL',parent:'ksl-prop-odds',file:'nfl_props.json',markets:['All markets','player_pass_yds','player_pass_tds','player_rush_yds','player_reception_yds','player_receptions','player_anytime_td']},
{sport:'NBA',parent:'ksl-nba',file:'nba_player_stats.json',markets:['Points','Rebounds','Assists','Threes','PRA','Pts+Reb','Pts+Ast','Reb+Ast','Minutes','Steals','Blocks','Turnovers']},
{sport:'NHL',parent:'ksl-nhl',file:'nhl_player_stats.json',markets:['Goals','Assists','Points','Shots on goal','Saves','Blocked shots','Hits']}
];
const style=document.createElement('style');style.textContent='.ksl-cheats{margin:18px 0;padding:16px;background:#0b1428;color:#eaf0ff;border:1px solid #293e6e;border-radius:13px}.ksl-cheats h2{font-size:clamp(21px,4vw,31px);font-weight:950;letter-spacing:-.7px;margin:0 0 8px;color:#f5f8ff;text-transform:uppercase}.ksl-cheats h2 em{color:#6c91fa;font-style:normal}.ksl-cheat-top{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;border-bottom:2px solid #435b9e;padding-bottom:10px}.ksl-cheat-sub{color:#94a9ce;font-size:12px}.ksl-cheat-filters{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.ksl-cheat-filters>*{background:#15213d;border:1px solid #3b568b;color:#e9f2ff;border-radius:7px;min-height:42px;padding:8px;max-width:100%}.ksl-cheat-scroll{overflow-x:auto;max-width:100%}.ksl-cheats table{width:100%;min-width:920px;border-collapse:collapse;font-size:12px}.ksl-cheats th{font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#90a8e1;text-align:left;border-bottom:1px solid #30446b;padding:12px 8px}.ksl-cheats td{padding:11px 8px;border-bottom:1px solid #202f51;white-space:nowrap}.ksl-cheats tbody tr:nth-child(even){background:#111e37}.ksl-cheats .ksl-cheat-player{font-weight:800;color:#f7faff}.ksl-cheats .ksl-cheat-team{font-size:10px;color:#9aaccd}.ksl-cheat-bars{display:flex;gap:3px;align-items:end;height:25px}.ksl-cheat-bars span{display:block;width:23px;min-height:4px;background:#4bd4a1;border-radius:2px}.ksl-cheat-bars span.miss{background:#f16c76}.ksl-cheat-bars span.unknown{background:#52627c}.ksl-cheat-score{border:1px solid #698bfa;border-radius:4px;padding:4px 8px;font-weight:900}.ksl-cheat-status{color:#a8b8d6;font-size:12px;line-height:1.5}.ksl-cheat-flag{color:#f5c779}.ksl-cheats .ksl-cheat-avg{color:#8de7b5;font-weight:700}';document.head.append(style);
const fmt=n=>Number.isFinite(n)?n.toFixed(1):'N/A';
const prob=p=>p<0?(-p)/(-p+100):100/(p+100);
const fmtOdds=p=>Number.isFinite(p)?(p>0?'+':'')+p:'N/A';
const number=n=>Number.isFinite(Number(n))?Number(n):null;
const build=(cfg)=>{
const parent=document.getElementById(cfg.parent);if(!parent)return;
const section=document.createElement('section');section.className='ksl-cheats';section.id='ksl-'+cfg.sport.toLowerCase()+'-cheats';
const top=document.createElement('div');top.className='ksl-cheat-top';
const title=document.createElement('h2');title.textContent=cfg.sport+' CHEAT SHEETS';
const date=document.createElement('span');date.className='ksl-cheat-sub';date.textContent='Historical trends · Saved data';
top.append(title,date);
const filters=document.createElement('div');filters.className='ksl-cheat-filters';
const market=document.createElement('select');market.setAttribute('aria-label',cfg.sport+' cheat sheet market');for(const m of cfg.markets)market.add(new Option(m.replaceAll('_',' ').toUpperCase(),m));
const threshold=document.createElement('input');threshold.type='number';threshold.step='0.5';threshold.min='0';threshold.value=cfg.sport==='NBA'?'15':cfg.sport==='NHL'?'0.5':'0';threshold.setAttribute('aria-label','Prop threshold');threshold.style.width='95px';
const search=document.createElement('input');search.placeholder='Search player';search.setAttribute('aria-label','Search player');search.style.width='160px';
const reload=document.createElement('button');reload.type='button';reload.textContent='Reload saved data';
filters.append(market,threshold,search,reload);if(cfg.sport==='NFL')threshold.hidden=true;
const status=document.createElement('p');status.className='ksl-cheat-status';status.setAttribute('role','status');
const scroll=document.createElement('div');scroll.className='ksl-cheat-scroll';
const table=document.createElement('table');const thead=document.createElement('thead');const tr=document.createElement('tr');
for(const h of ['#','Player / Team','Prop','Odds','Implied','Model score','Edge','Season avg','Last 5 avg','Last 10 avg','Last 5','Last 10','Consistency']){const th=document.createElement('th');th.textContent=h;tr.append(th)}thead.append(tr);const tbody=document.createElement('tbody');table.append(thead,tbody);scroll.append(table);
const note=document.createElement('p');note.className='ksl-cheat-status';note.textContent='Observed hit rates are historical only, not future hit probabilities. Model scores and edges require independently validated projections and exact sportsbook prices. Missing markets remain unavailable; no odds or projections are invented.';
section.append(top,filters,status,scroll,note);parent.prepend(section);
let feed=null;
function td(row,value,cls){const cell=document.createElement('td');if(cls)cell.className=cls;cell.textContent=String(value);row.append(cell);return cell}
function draw(){
tbody.replaceChildren();if(!feed)return;
const key=market.value;const query=search.value.trim().toLowerCase();let rows=[];
if(cfg.sport==='NFL'){
for(const x of feed.odds||[]){if(key!=='All markets'&&x.market!==key)continue;if(query&&!String(x.player).toLowerCase().includes(query))continue;rows.push({name:x.player,team:x.event,prop:x.market+' '+(x.selection||'')+(x.point==null?'':' '+x.point),price:x.price,stamp:x.updated_at,book:x.bookmaker})}
rows.sort((a,b)=>prob(b.price)-prob(a.price));
}else{
if((feed.unverified_markets||[]).includes(key)){status.textContent=key+' is not verified in this feed; no fabricated stats displayed.';return}
const limit=number(threshold.value);if(limit===null){status.textContent='Enter a valid threshold';return}
for(const x of feed.players||[]){if(query&&!x.name.toLowerCase().includes(query))continue;const games=(x.games||[]).filter(g=>Number.isFinite(g.values?.[key])).sort((a,b)=>String(b.date).localeCompare(String(a.date)));if(!games.length)continue;const values=games.map(g=>g.values[key]);const hits=values.map(v=>v>=limit);const avg=a=>a.length?a.reduce((s,v)=>s+v,0)/a.length:null;const rate=n=>hits.slice(0,n).length?Math.round(100*hits.slice(0,n).filter(Boolean).length/hits.slice(0,n).length):null;rows.push({name:x.name,team:x.team,prop:key+' ≥'+limit,avg:avg(values),avg5:avg(values.slice(0,5)),avg10:avg(values.slice(0,10)),rate5:rate(5),rate10:rate(10),hits:hits.slice(0,5),sample:values.length})}
rows.sort((a,b)=>(b.rate10??-1)-(a.rate10??-1)||(b.sample-a.sample));
}
status.textContent=rows.length+' entries · '+(feed.fetched_at||'unknown timestamp')+' · '+(cfg.sport==='NFL'?'Saved bookmaker prices only; no verified prop hit histories in this dataset.':'Historical box-score sample; no matched sportsbook prices.')+' Data may be stale.';
for(const [i,x] of rows.slice(0,100).entries()){
const row=document.createElement('tr');td(row,i+1);const player=td(row,x.name,'ksl-cheat-player');const team=document.createElement('div');team.className='ksl-cheat-team';team.textContent=x.team||'';player.append(team);td(row,x.prop);td(row,fmtOdds(x.price));td(row,Number.isFinite(x.price)?Math.round(prob(x.price)*100)+'%':'N/A');td(row,'N/A');td(row,'N/A');td(row,fmt(x.avg),'ksl-cheat-avg');td(row,fmt(x.avg5));td(row,fmt(x.avg10));td(row,x.rate5==null?'N/A':x.rate5+'%');td(row,x.rate10==null?'N/A':x.rate10+'%');
const barcell=document.createElement('td');const bars=document.createElement('div');bars.className='ksl-cheat-bars';if(x.hits){for(const hit of x.hits){const bar=document.createElement('span');if(!hit)bar.className='miss';bar.style.height='22px';bars.append(bar)}}else{const span=document.createElement('span');span.className='unknown';span.style.height='12px';bars.append(span)}barcell.append(bars);row.append(barcell);tbody.append(row)
}
}
async function load(){status.textContent='Loading saved '+cfg.sport+' data…';try{const res=await fetch('feed/'+cfg.file+'?t='+Date.now(),{cache:'no-store'});if(!res.ok)throw Error('No published feed');const data=await res.json();if(!Array.isArray(cfg.sport==='NFL'?data.odds:data.players))throw Error('Invalid feed');feed=data;draw()}catch(e){feed=null;tbody.replaceChildren();status.textContent='UNAVAILABLE: '+e.message}}
market.onchange=draw;threshold.oninput=draw;search.oninput=draw;reload.onclick=load;load();
};
for(const cfg of defs)build(cfg);
})();