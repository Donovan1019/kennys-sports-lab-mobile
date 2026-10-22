(()=>{'use strict';
const list=document.getElementById('ksl-context-games'),sport=document.getElementById('sport');if(!list||!sport)return;
const paths={NBA:'nba_player_stats.json',NFL:'nfl_player_stats.json',NHL:'nhl_player_stats.json'};
const markets={NBA:['Points','Rebounds','Assists','Threes','PRA'],NFL:['Receptions','Receiving Yards','Rushing Yards','Passing Yards'],NHL:['Goals','Assists','Saves']};
const cache={};const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
function decorate(){
for(const item of list.querySelectorAll('details')){if(item.dataset.historyConnected)continue;item.dataset.historyConnected='1';
const block=document.createElement('div'),heading=document.createElement('p');heading.textContent='Player historical distribution · research only (no matchup adjustment)';
const player=document.createElement('input');player.placeholder='Exact player name';player.setAttribute('aria-label','Player name');
const select=document.createElement('select');for(const key of markets[sport.value]||[]){const o=document.createElement('option');o.value=key;o.textContent=key;select.append(o)}
const threshold=document.createElement('input');threshold.type='number';threshold.step='0.5';threshold.placeholder='Prop line';threshold.setAttribute('aria-label','Historical prop threshold');
const direction=document.createElement('select');for(const v of ['Over','Under']){const o=document.createElement('option');o.value=v;o.textContent=v;direction.append(o)}
const button=document.createElement('button');button.textContent='Analyze 10,000 historical draws';button.type='button';const out=document.createElement('p');out.setAttribute('aria-live','polite');
button.onclick=async()=>{out.textContent='Loading historical player games…';try{
const chosen=sport.value;if(!player.value.trim()||threshold.value==='')throw Error('Enter player and threshold');
const value=Number(threshold.value);if(!Number.isFinite(value))throw Error('Invalid line');
if(!cache[chosen]){const response=await fetch('./feed/'+paths[chosen],{cache:'no-store'});if(!response.ok)throw Error('HTTP '+response.status);const data=await response.json();if(!Array.isArray(data.players))throw Error('Invalid player feed');cache[chosen]=data.players}
const matches=cache[chosen].filter(p=>norm(p.name)===norm(player.value));if(matches.length!==1)throw Error(matches.length?'Ambiguous player name':'Player not found');
const p=matches[0],key=select.value;
const games=(p.games||[]).filter(g=>g.values&&g.values[key]!==null&&g.values[key]!==''&&Object.prototype.hasOwnProperty.call(g.values,key)&&Number.isFinite(Number(g.values[key]))&&Number.isFinite(Date.parse(g.date))&&Date.parse(g.date)<Date.now()).sort((a,b)=>Date.parse(b.date)-Date.parse(a.date)).slice(0,30);
if(games.length<15)throw Error('Only '+games.length+' valid games; minimum 15');
const values=games.map(g=>Number(g.values[key]));let hits=0,push=0;const seed=[...p.name+key+String(value)].reduce((n,c)=>(Math.imul(n,31)+c.charCodeAt(0))|0,23);let state=seed;
for(let i=0;i<10000;i++){state=(Math.imul(state,1664525)+1013904223)|0;const x=values[Math.floor((state>>>0)/4294967296*values.length)];if(x===value)push++;else if(direction.value==='Over'?x>value:x<value)hits++}
out.textContent='HISTORICAL ONLY · '+p.name+' · '+direction.value+' '+value+' '+key+' · '+(hits/100).toFixed(1)+'% sampled wins · '+(push/100).toFixed(1)+'% pushes · '+games.length+' past games. Not calibrated, opponent-adjusted, or a green recommendation.';
}catch(e){out.textContent='UNAVAILABLE: '+e.message}};
block.append(heading,player,select,threshold,direction,button,out);item.append(block);
}}
const observer=new MutationObserver(decorate);observer.observe(list,{childList:true});sport.addEventListener('change',()=>{cache.NBA=null;cache.NFL=null;cache.NHL=null});decorate();
})();