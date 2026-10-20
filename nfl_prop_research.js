/* Historical prop research: verified game logs + manually supplied bookmaker price.
   Historical rates are descriptive only, never calibrated forecasts or betting EV. */
(()=>{'use strict';
const panel=document.createElement('section');panel.id='ksl-prop-research';
panel.innerHTML='<h2>NFL Player Prop Research</h2><p class="ksl-pr-note">Compare a verified historical threshold with a manually entered sportsbook price. Historical frequency is NOT a predictive probability, and break-even is NOT expected value. No automatic player-prop odds are connected.</p><div class="ksl-pr-fields"><label>Player<input id="ksl-pr-player" placeholder="Exact or partial player name"></label><label>Market<select id="ksl-pr-market"><option>Receiving yards</option><option>Receptions</option><option>Rushing yards</option><option>Passing yards</option><option>Passing touchdowns</option><option>Rushing touchdowns</option><option>Receiving touchdowns</option></select></label><label>Season<select id="ksl-pr-season"><option>2026</option><option>2025</option><option value="all">2025 + 2026</option></select></label><label>Last games<select id="ksl-pr-window"><option>3</option><option>5</option><option selected>10</option><option>20</option></select></label><label>Over line<input id="ksl-pr-line" type="number" min="0" step=".5" value="49.5"></label><label>Book<select id="ksl-pr-book"><option>FanDuel</option><option>DraftKings</option><option>Onyx</option><option>Other</option></select></label><label>American odds<input id="ksl-pr-price" type="number" placeholder="-110"></label></div><button id="ksl-pr-check" type="button">Analyze verified game logs</button><p id="ksl-pr-status" role="status" class="ksl-pr-note">Enter a player and a verified sportsbook line.</p><div id="ksl-pr-results"></div>';
const style=document.createElement('style');style.textContent='#ksl-prop-research{background:#101a17;border:1px solid #2a5744;border-radius:14px;margin:18px 0;padding:16px}#ksl-prop-research h2{color:#70ef91}#ksl-prop-research .ksl-pr-note{color:#b4c6bb;font-size:13px;line-height:1.5}#ksl-prop-research .ksl-pr-fields{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}#ksl-prop-research label{flex:1 1 140px;font-size:12px;color:#c9d7cd}#ksl-prop-research input,#ksl-prop-research select{display:block;width:100%;min-height:42px;margin-top:5px;background:#111e17;color:white;border:1px solid #3a6048;border-radius:8px;padding:8px}#ksl-prop-research button{min-height:46px;background:#25bd77;color:#06120d;font-weight:800;border:0;border-radius:9px;padding:10px 15px}#ksl-pr-results article{border:1px solid #355643;border-radius:10px;padding:10px;margin:10px 0}';document.head.append(style);(document.querySelector('main')||document.body).prepend(panel);
const $=id=>document.getElementById(id);
const defaults={'Receiving yards':49.5,'Receptions':2.5,'Rushing yards':49.5,'Passing yards':199.5,'Passing touchdowns':0.5,'Rushing touchdowns':0.5,'Receiving touchdowns':0.5};
$('ksl-pr-market').onchange=()=>{$('ksl-pr-line').value=defaults[$('ksl-pr-market').value]};
$('ksl-pr-check').onclick=async()=>{
 const status=$('ksl-pr-status'),out=$('ksl-pr-results');out.replaceChildren();
 const q=$('ksl-pr-player').value.trim().toLowerCase(),market=$('ksl-pr-market').value,season=$('ksl-pr-season').value,window=Number($('ksl-pr-window').value);
 const lineRaw=$('ksl-pr-line').value.trim(),priceRaw=$('ksl-pr-price').value.trim(),line=Number(lineRaw),price=Number(priceRaw);
 if(q.length<2||!lineRaw||!Number.isFinite(line)||line<0){status.textContent='Enter a player name and a valid nonnegative prop line.';return}
 if(priceRaw&&(!Number.isFinite(price)||!(price<=-100||price>=100))){status.textContent='Enter valid American odds (at most -100 or at least +100), or leave blank.';return}
 status.textContent='Loading published NFL game logs…';
 try{
  const response=await fetch('./feed/nfl_player_stats.json?t='+Date.now(),{cache:'no-store'});
  if(!response.ok)throw Error('Verified NFL game-log feed unavailable');
  const data=await response.json();
  if(data.source!=='nflverse-stats-player-week'||!Array.isArray(data.players))throw Error('Unexpected player data format');
  const matches=data.players.filter(p=>p.name.toLowerCase().includes(q)).slice(0,12);
  if(!matches.length){status.textContent='No matching verified player found.';return}
  const breakEven=priceRaw?(price<0?-price/(100-price):100/(price+100)):null;
  for(const p of matches){
   const games=p.games.filter(g=>(season==='all'||String(g.season)===season)&&Number.isFinite(g.values?.[market])).slice(-window);
   const hits=games.filter(g=>g.values[market]>line).length;
   const article=document.createElement('article');
   const title=document.createElement('strong');title.textContent=p.name+' · '+p.team;article.append(title);
   const info=document.createElement('p');info.textContent=games.length?'Historical OVER '+line+' '+market+': '+hits+'/'+games.length+' ('+(100*hits/games.length).toFixed(1)+'%) · '+season+' · values '+games.map(g=>g.values[market]).join(', '):'No qualifying games for this player, market and season.';article.append(info);
   if(breakEven!==null){const odds=document.createElement('p');odds.textContent=$('ksl-pr-book').value+' '+(price>0?'+':'')+price+' · bookmaker break-even '+(breakEven*100).toFixed(2)+'%. Price is manually entered and UNVERIFIED. Historical hit rate is NOT a forecast; EV unavailable.';article.append(odds)}
   out.append(article);
  }
  status.textContent='Source: '+data.source+' · '+data.fetched_at+' · '+matches.length+' matching players · strict OVER (greater than line). Historical descriptive research only.';
 }catch(e){status.textContent='UNAVAILABLE: '+e.message}
};
})();