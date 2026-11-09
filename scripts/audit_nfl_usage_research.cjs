#!/usr/bin/env node
'use strict';
// Free offline player-usage research. No assumed active status, no betting-ready projections.
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const stats=JSON.parse(fs.readFileSync(path.join(root,'feed/nfl_player_stats.json'),'utf8'));
const metrics={'QB':['Passing yards','Passing touchdowns','Pass Attempts','Completions','Rushing yards','Interceptions'],'RB':['Rushing yards','Rush Attempts','Receiving yards','Receptions'],'WR':['Receiving yards','Receptions','Targets'],'TE':['Receiving yards','Receptions','Targets']};
const now=new Date().toISOString();
const report={generated_at:now,status:'RESEARCH_ONLY',betting_eligible:false,source:stats.source,players_examined:0,profiles:[],blockers:{missing_current_games:0,insufficient_samples:0,missing_market_values:0,injury_and_active_role_unverified:0}};
for(const p of stats.players||[]){
 const position=String(p.position||'').toUpperCase();if(!metrics[position])continue;report.players_examined++;
 const games=(p.games||[]).filter(g=>g.season===2026&&g.season_type==='REG'&&g.game_id&&Number.isInteger(Number(g.week))).sort((a,b)=>Number(b.week)-Number(a.week));
 if(!games.length){report.blockers.missing_current_games++;continue}
 if(games.length<5){report.blockers.insufficient_samples++;continue}
 const market={};
 for(const name of metrics[position]){
  const valid=games.filter(g=>g.values&&g.values[name]!==null&&g.values[name]!==''&&Number.isFinite(Number(g.values[name])));
  if(valid.length<5){report.blockers.missing_market_values++;continue}
  const last=valid.slice(0,3).map(g=>Number(g.values[name]));
  const base=valid.slice(3,10).map(g=>Number(g.values[name]));
  if(base.length<2)continue;
  const avg=a=>a.reduce((x,y)=>x+y,0)/a.length;
  market[name]={recent_three_mean:avg(last),prior_mean:avg(base),change_pct:avg(base)>0?100*(avg(last)/avg(base)-1):null,sample_games:valid.length,forecast_eligible:false};
 }
 if(!Object.keys(market).length)continue;
 report.blockers.injury_and_active_role_unverified++;
 report.profiles.push({name:p.name,position,team:p.team||null,latest_week:games[0].week,markets:market,injury_verified:false,role_verified:false,betting_eligible:false});
}
report.profiles.sort((a,b)=>a.position.localeCompare(b.position)||a.name.localeCompare(b.name));
fs.writeFileSync(path.join(root,'feed/nfl_usage_research.json'),JSON.stringify(report,null,2)+'\n');
console.log('NFL offline usage audit',JSON.stringify({players:report.players_examined,profiles:report.profiles.length,blockers:report.blockers}));
