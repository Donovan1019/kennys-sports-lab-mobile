#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
const norm=x=>String(x||'').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'').replace(/sergei/g,'sergey');
const valid=x=>Number.isInteger(x)&&Math.abs(x)>=100;
function build(events,snapshot,now=Date.now()){
 const rows=[],unmatched=[],seen=new Set();
 for(const card of snapshot.cards||[]){
  const date=String(card.data?.event?.starts_at||'').slice(0,10);
  const candidates=(events.events||[]).filter(e=>String(e.date).slice(0,10)===date);
  for(const item of card.data?.fights||[]){
   const names=[norm(item.fighter_a?.name),norm(item.fighter_b?.name)];
   if(names.some(n=>!n)){unmatched.push({fightId:item.fight_id,reason:'MISSING_FIGHTER'});continue}
   const matches=candidates.flatMap(e=>(e.bouts||[]).filter(b=>b.status==='scheduled'&&
     (b.fighters||[]).length===2&&b.fighters.every(f=>names.includes(norm(f.name||f.slug))))
     .map(b=>({event:e,bout:b})));
   if(matches.length!==1){unmatched.push({fightId:item.fight_id,reason:matches.length?'AMBIGUOUS_MATCH':'NO_EXACT_MATCH'});continue}
   const {event,bout}=matches[0],p=item.consensus;
   if(!p||!valid(p.a?.american)||!valid(p.b?.american)){unmatched.push({fightId:item.fight_id,reason:'NO_VALID_MONEYLINE'});continue}
   const ts=Date.parse(p.recorded_at);
   if(!Number.isFinite(ts)||ts>now+300000||now-ts>7200000){unmatched.push({fightId:item.fight_id,reason:'STALE_CONSENSUS'});continue}
   if(seen.has(bout.id)){unmatched.push({fightId:item.fight_id,reason:'DUPLICATE_BOUT'});continue}
   seen.add(bout.id);
   const totals=(item.props?.total_rounds||[]).filter(t=>Number.isFinite(t.line)&&valid(t.over?.american)&&valid(t.under?.american)&&Number.isFinite(Date.parse(t.recorded_at))&&Date.parse(t.recorded_at)<=now+300000&&now-Date.parse(t.recorded_at)<=7200000).map(t=>({line:t.line,over:{american:t.over.american},under:{american:t.under.american},recordedAt:t.recorded_at,sources:t.sources||0}));
   rows.push({totalRounds:totals,fightId:bout.id,eventId:event.id,sourceFightId:item.fight_id,source:'ufcalendar-consensus',book:null,bookVerified:false,bettingReady:false,recordedAt:p.recorded_at,sources:p.sources||0,markets:[
    {selection:item.fighter_a.name,american:p.a.american},
    {selection:item.fighter_b.name,american:p.b.american}
   ],fairProbabilityA:Number.isFinite(p.fair_probability_a)?p.fair_probability_a:null});
  }
 }
 return {schemaVersion:1,source:'ufcalendar-consensus-matched',generatedAt:new Date(now).toISOString(),matched:rows.length,unmatched:unmatched.length,rows,exceptions:unmatched,bettingReady:false};
}
if(require.main===module){
 const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
 const out=build(read('data/pfl/events.json'),read('data/pfl/ufcalendar-odds.json'));
 fs.writeFileSync('data/pfl/consensus-markets.json',JSON.stringify(out,null,2)+'\n');
 console.log('PFL consensus mapping:',JSON.stringify({matched:out.matched,unmatched:out.unmatched,reasons:out.exceptions.reduce((a,x)=>(a[x.reason]=(a[x.reason]||0)+1,a),{})}));
}
module.exports={build,norm};
