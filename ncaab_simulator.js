/* NCAA provisional score simulator. Not a validated predictive model. */
(function(){
'use strict';
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>Number(n).toFixed(1);
const norm=n=>String(n||'').toLowerCase().replace(/[^a-z0-9]/g,'');
function randNormal(){let u=0,v=0;while(!u)u=Math.random();while(!v)v=Math.random();return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v)}
function build(primary,date,odds){
 const data=primary?.data||{},records=new Map((data.standings||[]).map(r=>[r.team?.team_id,r]));
 const teams=new Map((data.teams||[]).map(t=>[t.team_id,t]));
 const games=(data.games||[]).filter(g=>g.date===date),output=[];
 for(const g of games){
  const a=records.get(g.away_team?.team_id),h=records.get(g.home_team?.team_id);
  if(!a||!h||a.games_played<5||h.games_played<5||![a.points_for,a.points_against,h.points_for,h.points_against].every(Number.isFinite)){output.push({g,status:'INSUFFICIENT_SAMPLE'});continue}
  const aOff=a.points_for/a.games_played,aDef=a.points_against/a.games_played,hOff=h.points_for/h.games_played,hDef=h.points_against/h.games_played;
  // Simple blended scoring scenario; no possession, opponent, schedule or injury adjustments.
  const awayMean=(aOff+hDef)/2,homeMean=(hOff+aDef)/2+2.5;
  const n=5000,away=[],home=[];let homeWins=0,awayWins=0,ties=0;
  for(let i=0;i<n;i++){const shared=randNormal()*7,as=Math.max(0,awayMean+shared+randNormal()*9),hs=Math.max(0,homeMean+shared+randNormal()*9);away.push(as);home.push(hs);if(hs>as)homeWins++;else if(as>hs)awayWins++;else ties++}
  const sorted=x=>x.sort((a,b)=>a-b),quant=(x,p)=>x[Math.floor((x.length-1)*p)];
  const aSorted=sorted(away),hSorted=sorted(home),totals=sorted(away.map((x,i)=>x+home[i]));
  output.push({g,status:'EXPLORATORY',n,awayMean,homeMean,homeWins,awayWins,ties,awayRange:[quant(aSorted,.1),quant(aSorted,.9)],homeRange:[quant(hSorted,.1),quant(hSorted,.9)],totalRange:[quant(totals,.1),quant(totals,.9)],totalMean:awayMean+homeMean,awayConference:teams.get(g.away_team.team_id)?.conference,homeConference:teams.get(g.home_team.team_id)?.conference});
 }
 return output;
}
function render(primary,date,odds){
 const list=build(primary,date,odds);
 return '<h2>Exploratory NCAA score scenarios ('+list.length+' games)</h2><div class="panel"><strong>Research mode — not betting-ready</strong><p>5,000 Monte Carlo score scenarios per eligible matchup using current-season raw scoring and points allowed. Requires at least five games per team. Not possession-adjusted, opponent-adjusted, calibrated or backtested. Do not use these frequencies as win probabilities or EV.</p></div>'+(list.map(x=>{const g=x.g,header='<strong>'+esc(g.away_team?.name)+' @ '+esc(g.home_team?.name)+'</strong>';if(x.status!=='EXPLORATORY')return '<article class="game">'+header+'<p class="sgp-note">INSUFFICIENT SAMPLE — at least five completed games and scoring records required for each team.</p></article>';return '<article class="game">'+header+'<div class="grid"><div class="stat"><small>'+esc(g.away_team.name)+' raw score scenario</small><div><strong>'+fmt(x.awayMean)+'</strong></div><small>10–90% scenario interval: '+fmt(x.awayRange[0])+'–'+fmt(x.awayRange[1])+'</small></div><div class="stat"><small>'+esc(g.home_team.name)+' raw score scenario</small><div><strong>'+fmt(x.homeMean)+'</strong></div><small>10–90% scenario interval: '+fmt(x.homeRange[0])+'–'+fmt(x.homeRange[1])+'</small></div><div class="stat"><small>Combined score scenario</small><div><strong>'+fmt(x.totalMean)+'</strong></div><small>10–90% interval: '+fmt(x.totalRange[0])+'–'+fmt(x.totalRange[1])+'</small></div></div><p class="sgp-note">EXPLORATORY ONLY · '+x.n.toLocaleString()+' simulations · no calibrated odds, EV or Diamond status</p></article>'}).join('')||'<div class="panel">No games available for this date.</div>');
}
window.NCAABSimulator={build,render};
})();