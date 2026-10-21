/* Top Players: display only independently verified, eligible player betting recommendations. */
(()=>{'use strict';
const main=document.querySelector('main');if(!main)return;
const sports=[['NFL','americanfootball_nfl'],['NBA','basketball_nba'],['NHL','icehockey_nhl']];
const decimalProfit=odds=>odds>0?odds/100:100/(-odds);
const valid=e=>e&&e.bet_eligible===true&&e.status==='verified'&&e.verified_market===true&&e.simulation_verified===true&&e.lineup_verified===true&&e.market_fresh===true&&e.is_player_prop===true&&typeof e.player==='string'&&e.player.trim()&&typeof e.market==='string'&&e.market.trim()&&typeof e.selection==='string'&&e.selection.trim()&&Number.isFinite(e.point)&&Number.isFinite(e.hit_probability)&&e.hit_probability>0&&e.hit_probability<1&&Number.isFinite(e.market_odds_american)&&e.market_odds_american!==0&&Number.isFinite(e.expected_value)&&e.expected_value>0&&Math.abs(e.hit_probability*decimalProfit(e.market_odds_american)-(1-e.hit_probability)-e.expected_value)<0.02&&typeof e.verified_at==='string'&&Number.isFinite(Date.parse(e.verified_at))&&Date.now()-Date.parse(e.verified_at)<3600000&&Date.parse(e.verified_at)<=Date.now();
for(const [sport,slug] of sports){
 const root=document.createElement('section');root.id='ksl-'+sport.toLowerCase()+'-top-players';root.className='ksl-top-players';root.style.cssText='border:2px solid #4ca96d;border-radius:14px;padding:16px;margin:12px 0 16px;background:#10221d;color:#ecfff0';
 const title=document.createElement('h2');title.textContent=sport+' · Top Players · Verified Betting Recommendations';root.append(title);
 const note=document.createElement('p');note.textContent='Strictly verified player props only: current line and odds, player status, validated simulation, probability, positive EV, and recent verification. Archived trends alone never qualify.';root.append(note);
 const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Checking verified player recommendations…';root.append(status);
 const list=document.createElement('div');root.append(list);main.prepend(root);
 (async()=>{try{
  const response=await fetch('./feed/'+slug+'_pregame_research.json',{cache:'no-store'});if(!response.ok)throw Error('Research unavailable');
  const data=await response.json();const eligible=(data.events||[]).filter(valid).sort((a,b)=>b.expected_value-a.expected_value).slice(0,10);
  if(!eligible.length){status.textContent='NO VERIFIED PLAYER BETTING RECOMMENDATIONS — current data does not meet required eligibility checks.';return;}
  status.textContent=eligible.length+' verified player recommendation'+(eligible.length===1?'':'s')+' · confirm prices again before betting';
  for(const [i,e] of eligible.entries()){const row=document.createElement('div');row.style.cssText='border-top:1px solid #365e49;padding:10px 0';const heading=document.createElement('strong');heading.textContent=(i+1)+'. '+e.player+' · '+e.market+' '+e.selection+' '+e.point;const details=document.createElement('div');details.textContent='Odds '+(e.market_odds_american>0?'+':'')+e.market_odds_american+' · model '+(e.hit_probability*100).toFixed(1)+'% · EV '+(e.expected_value*100).toFixed(1)+'% · verified '+e.verified_at;details.style.cssText='font-size:13px;color:#b7d3bf';row.append(heading,details);list.append(row);}
 }catch(err){status.textContent='NO VERIFIED PLAYER BETTING RECOMMENDATIONS — unable to verify current source.';}})();
}
})();