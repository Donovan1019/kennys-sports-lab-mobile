#!/usr/bin/env node
'use strict';
// Offline, source-backed SGP research audit. Never emits betting-ready picks.
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.resolve(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const stats=read('feed/nfl_player_stats.json'),feed=read('feed/nfl_props.json');
const ctx={window:{}};vm.runInNewContext(fs.readFileSync(path.join(root,'nfl_sgp_joint_bootstrap.js'),'utf8'),ctx);
const joint=ctx.window.KSLSGPJoint.joint;
const now=Date.now(),pairs=new Map();
for(const o of feed.odds||[]){
 if(!o||!['draftkings','fanduel'].includes(o.bookmaker)||!['Over','Under'].includes(o.selection)||!o.event_id||!o.player||!Number.isFinite(Number(o.point))||!Number.isFinite(Number(o.price))||!Number.isFinite(Date.parse(o.commence_time))||!Number.isFinite(Date.parse(o.updated_at))||Date.parse(o.commence_time)<=now||Date.parse(o.updated_at)>now||now-Date.parse(o.updated_at)>30*60000)continue;
 const k=[o.event_id,o.bookmaker,o.player,o.market,o.point].join('|');
 if(!pairs.has(k))pairs.set(k,{});
 pairs.get(k)[o.selection]=o;
}
const grouped=new Map();
for(const p of pairs.values()){
 if(!p.Over||!p.Under)continue;
 const o=p.Over,k=o.event_id+'|'+o.bookmaker;
 if(!grouped.has(k))grouped.set(k,[]);
 grouped.get(k).push(o);
}
const report={generated_at:new Date().toISOString(),status:'RESEARCH_ONLY',betting_eligible:false,source:'verified historical player logs + timestamped published DK/FD quotes',games_examined:grouped.size,combinations_examined:0,simulated:0,blocked:0,reasons:{},samples:[]};
const blocked=reason=>{report.blocked++;report.reasons[reason]=(report.reasons[reason]||0)+1};
for(const [game,rows] of grouped){
 const unique=[...new Map(rows.map(x=>[x.player+'|'+x.market,x])).values()].slice(0,16);
 for(let i=0;i<unique.length;i++)for(let j=i+1;j<unique.length;j++){
  if(report.combinations_examined>=200)break;
  const a=unique[i],b=unique[j];if(a.player===b.player)continue;
  report.combinations_examined++;
  const legs=[a,b].map(x=>({player:x.player,market:x.market,selection:'Over',point:x.point}));
  const result=joint(stats,legs,{trials:2000,seed:game+'|'+i+'|'+j});
  if(result.status==='BLOCKED'){blocked(result.reason||'simulator blocked');continue}
  report.simulated++;
  if(report.samples.length<12)report.samples.push({event_id:a.event_id,bookmaker:a.bookmaker,legs,simulation_status:result.status,paired_events:result.paired_events,betting_eligible:false,official_combined_price_available:false});
 }
}
const dest=path.join(root,'feed/nfl_sgp_research_audit.json');
fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
console.log('NFL SGP research audit:',JSON.stringify({games:report.games_examined,examined:report.combinations_examined,simulated:report.simulated,blocked:report.blocked}));
