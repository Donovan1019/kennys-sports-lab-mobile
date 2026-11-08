(()=>{
'use strict';
const root=document.getElementById('nfl-qb-unders');if(!root)return;
const status=document.getElementById('nfl-qb-unders-status'),out=document.getElementById('nfl-qb-unders-results');
const market=document.getElementById('nfl-qb-unders-market'),minimum=document.getElementById('nfl-qb-unders-sample');
const fields={
'Passing Touchdowns':['passingtouchdowns','passingtds','passtds'],
'Passing Yards':['passingyards','passyds','passyards'],
'Rushing Yards':['rushingyards','rushyds','rushyards'],
'Interceptions':['interceptions','passinginterceptions','passint'],
'Pass Attempts':['passattempts','passingattempts','passatt','passingatt'],
'Pass Completions':['passcompletions','passingcompletions','completions','passcmp'],
'Rush Attempts':['rushattempts','rushingattempts','carries'],
'Sacks Taken':['sackstaken','times sacked','qb sacks taken'],
'Completion Percentage':['completionpercentage','completionpct'],
'Yards Per Attempt':['yardsperattempt','passingyardsperattempt']
};
const key=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const get=(v,m)=>{const k=Object.keys(v||{}).find(k=>fields[m].map(key).includes(key(k)));if(!k||v[k]===null||v[k]==='')return null;const n=Number(v[k]);return Number.isFinite(n)?n:null};
const num=(n)=>Number(n).toFixed(1);
let players=[],fetched='';
function render(){
out.replaceChildren();const chosen=market.value,required=Number(minimum.value),rank=[];
for(const p of players){
if(String(p.position||'').toUpperCase()!=='QB')continue;
const games=(p.games||[]).filter(g=>g&&g.values&&g.season_type!=='POST'&&g.season_type!==3&&g.season_type!=='PRE'&&g.season_type!==1&&g.season_type!=='PRESEASON')
.sort((a,b)=>{const index=g=>Number.isFinite(Number(g.season))&&Number.isFinite(Number(g.week))?Number(g.season)*100+Number(g.week):Date.parse(g.date)||0;return index(b)-index(a)});
const sample=games.slice(0,required);if(sample.length!==required)continue;
const recent=sample.slice(0,3).map(g=>get(g.values,chosen));
const baseline=sample.slice(3).map(g=>get(g.values,chosen));
if(recent.some(v=>v===null)||baseline.some(v=>v===null))continue;
const r=recent.reduce((a,b)=>a+b,0)/3,b=baseline.reduce((a,b)=>a+b,0)/baseline.length;
if(b<=0)continue;const delta=(r-b)/b;
const direction=chosen==='Interceptions'?'OVER':'UNDER';
const eligible=direction==='OVER'?delta>=.15:delta<=-.15;
if(!eligible)continue;
rank.push({p,recent:r,baseline:b,delta,direction,n:required,last:recent[0],values:sample.map(g=>get(g.values,chosen))});
}
rank.sort((a,b)=>Math.abs(b.delta)-Math.abs(a.delta));
status.textContent=rank.length+' historical '+(chosen==='Interceptions'?'rising-turnover':'declining')+' trends · '+players.filter(p=>String(p.position||'').toUpperCase()==='QB').length+' QB profiles · feed '+fetched+' · RESEARCH ONLY';
if(!rank.length){const p=document.createElement('p');p.textContent='No qualifying QB trend with complete recent and baseline game logs for this market. Missing values are never treated as zero.';out.append(p);return}
for(const x of rank.slice(0,20)){
const card=document.createElement('article');card.className='ksl-qb-under-card';
const heading=document.createElement('h3');heading.textContent=x.p.name+' · '+chosen+' · '+x.direction+' trend';
const detail=document.createElement('p');detail.textContent=(x.p.team||'Team unavailable')+' · Last 3 avg '+num(x.recent)+' vs previous '+(x.n-3)+' avg '+num(x.baseline)+' · '+(x.delta*100).toFixed(0)+'% change';
const sub=document.createElement('p');sub.textContent='Recorded games: '+x.n+' · Most recent: '+x.last+' · Trend only. No verified opponent, starting role, injury status, sportsbook line, odds, simulation, or EV attached.';
const context=document.createElement('p');context.className='ksl-qb-guardrail';context.textContent='CHECK BEFORE BETTING: Confirm starter and official inactives, projected attempts and pace, opponent coverage/pass rush, weather, line movement, and sportsbook settlement. Three-game decline alone is not a calibrated edge.';
card.append(heading,detail,sub,context);out.append(card);
}
}
async function load(){status.textContent='Loading verified QB game logs…';try{
const r=await fetch('./feed/nfl_player_stats.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);
const data=await r.json();if(!Array.isArray(data.players))throw Error('Missing player game logs');
players=data.players;fetched=data.fetched_at||'unknown';render();
}catch(e){status.textContent='QB trends unavailable: '+e.message+' · No projections or odds fabricated';out.replaceChildren()}}
market.addEventListener('change',render);minimum.addEventListener('change',render);
document.getElementById('nfl-qb-unders-refresh').addEventListener('click',load);
load();
})();