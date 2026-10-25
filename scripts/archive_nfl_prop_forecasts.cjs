#!/usr/bin/env node
'use strict';
// Append-only pregame prop forecasts. Never synthesize model probabilities from outcomes.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const input=process.argv[2],dest=path.join(root,'feed','nfl_prop_forecast_ledger.json');
if(!input){console.error('Usage: node scripts/archive_nfl_prop_forecasts.cjs pregame-export.json');process.exit(2)}
let incoming;try{incoming=JSON.parse(fs.readFileSync(input,'utf8'))}catch(e){console.error(e.message);process.exit(2)}
if(!Array.isArray(incoming)||!incoming.length){console.error('REJECTED: empty forecast export');process.exit(2)}
const existing=fs.existsSync(dest)?JSON.parse(fs.readFileSync(dest,'utf8')):{status:'RESEARCH_ONLY',forecasts:[]};
if(!Array.isArray(existing.forecasts)){console.error('REJECTED: malformed existing ledger');process.exit(2)}
const now=Date.now(),seen=new Map(existing.forecasts.map(x=>[x.forecast_id,x])),errors=[];
const validOdds=x=>Number.isInteger(x)&&(x>=100||x<=-100);
const validMarket=x=>['player_pass_yds','player_rush_yds','player_reception_yds','player_receptions','player_pass_tds','player_rush_tds','player_anytime_td','player_rec_tds','Passing Yards','Rushing Yards','Receiving Yards','Receptions','Passing Touchdowns','Rushing Touchdowns','Receiving Touchdowns','Anytime Touchdown'].includes(x);
const implied=x=>x>0?100/(x+100):-x/(-x+100);
for(const [i,x] of incoming.entries()){
 const at=Date.parse(x.forecast_at),start=Date.parse(x.kickoff),quote=Date.parse(x.quoted_at);
 if(!x.forecast_id||!x.event_id||!x.player||!validMarket(x.market)||!x.source_commit||!x.source_repository||!Number.isFinite(x.line)||!(x.model_probability>0&&x.model_probability<1)||!validOdds(x.over_odds)||!validOdds(x.under_odds)||implied(x.over_odds)+implied(x.under_odds)<=1||!Number.isFinite(at)||!Number.isFinite(start)||!Number.isFinite(quote)||at>now||at>=start||now>=start||quote>at||at-quote>21600000){errors.push('invalid pregame forecast '+i);continue}
 if(x.source_repository!=='Donovan1019/sports-model-foundation'){errors.push('unknown forecast provenance '+i);continue}
 const old=seen.get(x.forecast_id);if(old&&JSON.stringify(old)!==JSON.stringify(x)){errors.push('conflicting forecast ID '+i);continue}
 seen.set(x.forecast_id,x);
}
if(errors.length){console.error(JSON.stringify({status:'REJECTED',errors},null,2));process.exit(1)}
fs.mkdirSync(path.dirname(dest),{recursive:true});
fs.writeFileSync(dest,JSON.stringify({status:'RESEARCH_ONLY',forecasts:[...seen.values()]},null,2)+'\n');
console.log(JSON.stringify({status:'ARCHIVED_RESEARCH_ONLY',total:seen.size,betting_ready:false}));
