#!/usr/bin/env node
'use strict';
// Conservative first-party pregame export. 2025 regular-season observations only:
// avoids leaking 2026 future results when historical rows lack game dates.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const odds=read('feed/nfl_props.json'),history=read('feed/nfl_player_stats.json');
const now=Date.now(),commit=process.env.GITHUB_SHA||'local-uncommitted';
const mapping={'player_pass_yds':'Passing yards','player_rush_yds':'Rushing yards','player_reception_yds':'Receiving yards','player_receptions':'Receptions','player_pass_tds':'Passing touchdowns'};
const books=new Map(),players=new Map();
for(const p of history.players||[])players.set(String(p.name).toLowerCase().replace(/[^a-z]/g,''),p);
for(const o of odds.odds||[]){
 if(!mapping[o.market]||!['Over','Under'].includes(o.selection)||!Number.isFinite(o.point)||!Number.isInteger(o.price)||!o.event_id||!o.player||!o.bookmaker)continue;
 const key=[o.event_id,o.player,o.market,o.point,o.bookmaker].join('|');
 const entry=books.get(key)||{};entry[o.selection]=o;books.set(key,entry);
}
const validOdds=o=>Number.isInteger(o)&&(o>=100||o<=-100);
const implied=o=>o>0?100/(o+100):-o/(-o+100);
const output=[],reject={};
const skip=k=>{reject[k]=(reject[k]||0)+1};
for(const pair of books.values()){
 const over=pair.Over,under=pair.Under;
 if(!over||!under){skip('missing_two_way_quote');continue}
 const start=Date.parse(over.commence_time),qt=Date.parse(over.updated_at),ut=Date.parse(under.updated_at);
 if(!Number.isFinite(start)||start<=now||!Number.isFinite(qt)||!Number.isFinite(ut)||qt>now||ut>now||now-Math.min(qt,ut)>21600000||qt>=start||ut>=start){skip('stale_or_started');continue}
 if(!validOdds(over.price)||!validOdds(under.price)||implied(over.price)+implied(under.price)<=1){skip('invalid_odds');continue}
 const player=players.get(over.player.toLowerCase().replace(/[^a-z]/g,''));
 if(!player){skip('no_exact_player_history');continue}
 const metric=mapping[over.market];
 const values=(player.games||[]).filter(g=>g.season===2025&&g.season_type==='REG'&&Number.isFinite(g.values?.[metric])).map(g=>g.values[metric]);
 if(values.length<8){skip('insufficient_prior_season_games');continue}
 // No game or injury verification: explicitly RESEARCH ONLY.
 const probability=(values.filter(x=>x>over.point).length+1)/(values.length+2);
 const id=crypto.createHash('sha256').update([over.event_id,over.player,over.market,over.point,over.bookmaker,over.updated_at,under.updated_at].join('|')).digest('hex');
 output.push({forecast_id:id,event_id:over.event_id,player:over.player,market:over.market,line:over.point,model_probability:probability,over_odds:over.price,under_odds:under.price,quoted_at:new Date(Math.max(qt,ut)).toISOString(),forecast_at:new Date(now).toISOString(),kickoff:new Date(start).toISOString(),source_repository:'Donovan1019/kennys-sports-lab-mobile',source_commit:commit,bookmaker:over.bookmaker,model_version:'2025-prior-season-laplace-v1',research_only:true});
}
const dest=path.join(root,'feed','nfl_prop_forecast_inbox.json');
if(output.length){fs.writeFileSync(dest,JSON.stringify(output,null,2)+'\n')}
console.log(JSON.stringify({status:'RESEARCH_ONLY',created:output.length,rejected:reject,output:output.length?dest:null,betting_ready:false}));
