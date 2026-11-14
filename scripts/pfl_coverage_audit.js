#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
function audit(cito,ufcal){
const events=cito.events||[],other=ufcal.events||[];
const bouts=events.flatMap(e=>(e.bouts||[]).map(b=>({...b,eventId:e.id,eventName:e.name,eventDate:e.date})));
const ids=new Set(),issues=[];
for(const b of bouts){if(!b.id||ids.has(b.id))issues.push('Missing or duplicate bout ID: '+b.id);ids.add(b.id);
if(b.fighters.length!==2||b.fighters.some(f=>!f.slug||!f.name))issues.push('Incomplete fighter mapping: '+b.id);
if(![3,5].includes(b.scheduledRounds))issues.push('Invalid scheduled rounds: '+b.id);
if(b.status==='completed'&&(!b.method||!b.resultRound||!b.resultTime))issues.push('Incomplete historical result: '+b.id);
}
const day=s=>String(s||'').slice(0,10);
const cross=events.map(e=>({eventId:e.id,eventName:e.name,ufcalendarMatches:other.filter(o=>day(o.date)===day(e.date)).map(o=>({id:o.id,name:o.name})),boutCount:(e.bouts||[]).length}));
return {citoEvents:events.length,ufcalendarEvents:other.length,totalBouts:bouts.length,scheduledBouts:bouts.filter(b=>b.status==='scheduled').length,completedBouts:bouts.filter(b=>b.status==='completed').length,missingOfficialStats:bouts.filter(b=>!b.officialStats).length,marketOddsAvailable:0,cross,issues,bettingReady:false,reason:'No authenticated sportsbook prices or independently calibrated fighter probabilities in these API snapshots'};
}
if(require.main===module){const [a,b]=process.argv.slice(2);if(!a||!b)throw Error('Pass Cito and UFCalendar snapshot paths');const result=audit(JSON.parse(fs.readFileSync(a)),JSON.parse(fs.readFileSync(b)));console.log(JSON.stringify(result,null,2));if(result.issues.length)process.exitCode=1;}
module.exports={audit};
