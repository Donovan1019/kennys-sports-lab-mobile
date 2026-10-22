(()=>{'use strict';
const sport=document.getElementById('sport'),subject=document.getElementById('subject'),market=document.getElementById('market'),line=document.getElementById('line'),prob=document.getElementById('prob');
if(!sport||!subject||!market||!line||!prob)return;
const panel=document.createElement('div');panel.className='card';panel.innerHTML='<h2>Player distribution engine · 10,000 draws</h2><p>Historical empirical outcome distribution, independently computed from saved game logs. Not matchup-adjusted or calibrated; never qualifies a bet by itself.</p><button type="button" id="ksl-player-run">Simulate selected player market</button><p id="ksl-player-status" aria-live="polite">Select a player prop from the feed or enter a player, market, and threshold.</p>';
document.querySelector('main').append(panel);
const status=document.getElementById('ksl-player-status'),paths={NBA:'nba_player_stats.json',NFL:'nfl_player_stats.json',NHL:'nhl_player_stats.json'};
const aliases={NBA:{points:'Points',rebounds:'Rebounds',assists:'Assists',threes:'Threes',pra:'PRA'},NFL:{receptions:'Receptions',receiving_yards:'Receiving Yards',rushing_yards:'Rushing Yards',passing_yards:'Passing Yards'},NHL:{shots:'Shots on goal',shots_on_goal:'Shots on goal',goals:'Goals',assists:'Assists',points:'Points',saves:'Saves'}};
const normal=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const seedRand=seed=>()=>{seed=(Math.imul(seed,1664525)+1013904223)|0;return(seed>>>0)/4294967296};
document.getElementById('ksl-player-run').onclick=async()=>{
prob.value='';prob.dataset.provenance='';status.textContent='Loading saved player history…';
const name=subject.value.trim(),raw=market.value.toLowerCase(),threshold=Number(line.value);
if(!name||!line.value||!Number.isFinite(threshold)){status.textContent='UNAVAILABLE: Player and numeric threshold required.';return}
let key=null;for(const [alias,field] of Object.entries(aliases[sport.value]||{})){if(raw.includes(alias.replace(/_/g,' '))||raw.includes(alias)){key=field;break}}
if(!key){status.textContent='UNAVAILABLE: Unsupported or ambiguous player-stat market. No probability generated.';return}
try{const response=await fetch('./feed/'+paths[sport.value],{cache:'no-store'});if(!response.ok)throw Error('feed HTTP '+response.status);const data=await response.json();if(!Array.isArray(data.players))throw Error('player logs schema missing');
const p=data.players.find(x=>normal(x.name)===normal(name));if(!p)throw Error('Player not matched exactly in saved '+sport.value+' logs');
const rows=(p.games||[]).filter(g=>g&&g.values&&Number.isFinite(Number(g.values[key]))&&g.values[key]!==null&&g.date&&Date.parse(g.date)<Date.now()).sort((a,b)=>String(b.date).localeCompare(String(a.date))).slice(0,30);
const values=rows.map(g=>Number(g.values[key]));if(values.length<15)throw Error('fewer than 15 usable prior games for '+key);
const isUnder=/under|\bu\b/.test(raw),isOver=/over|\bo\b/.test(raw);if(!isUnder&&!isOver)throw Error('Specify Over or Under; ambiguous direction');
let seed=[...p.name+key+threshold].reduce((v,c)=>Math.imul(v,31)+c.charCodeAt(0)|0,98765),rand=seedRand(seed),hits=0;
for(let i=0;i<10000;i++){const x=values[Math.floor(rand()*values.length)];if(isUnder?x<threshold:x>threshold)hits++}
const rate=hits/10000;const chronological=rows.slice().reverse();let brier=0,baseline=0,checks=0;for(let j=15;j<chronological.length;j++){const prior=chronological.slice(0,j).map(g=>Number(g.values[key]));const target=isUnder?Number(chronological[j].values[key])<threshold:Number(chronological[j].values[key])>threshold;const historyHits=prior.filter(x=>isUnder?x<threshold:x>threshold).length;const predicted=(historyHits+2)/(prior.length+4);brier+=(predicted-Number(target))**2;baseline+=(0.5-Number(target))**2;checks++}const validation=checks>=10?'Walk-forward '+checks+' held-out predictions · Brier '+(brier/checks).toFixed(3)+' vs 50% baseline '+(baseline/checks).toFixed(3):'Walk-forward validation INSUFFICIENT ('+checks+' predictions; need 10).';status.textContent='HISTORICAL ONLY · '+p.name+' '+key+' '+(isUnder?'under ':'over ')+threshold+' · '+values.length+' past games · 10,000 empirical draws · '+(rate*100).toFixed(1)+'% sampled hit rate. NOT CALIBRATED, NOT BET ELIGIBLE. No probability entered into betting audit.';
}catch(e){status.textContent='UNAVAILABLE: '+e.message}
};
})();