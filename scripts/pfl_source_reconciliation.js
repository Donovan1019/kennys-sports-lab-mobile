#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
const day=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}/.test(s)?s.slice(0,10):null;
const norm=s=>typeof s==='string'?s.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,''):'';
function entries(x){if(Array.isArray(x))return x;if(!x||typeof x!=='object')return [];for(const k of ['items','events','fights','data','results']){if(x[k]){const a=entries(x[k]);if(a.length)return a}}return []}
function audit(cito,api){
 const fighters=new Map();
 for(const e of cito.events||[])for(const b of e.bouts||[])for(const f of b.fighters||[]){if(f?.slug)fighters.set(f.slug,{slug:f.slug,name:f.name||null})}
 const eventRows=[...entries(api.schedule),...entries(api.events)];
 const ids=new Set(),duplicates=[],matched=[],unmatched=[],ambiguous=[];
 const citoEvents=(cito.events||[]).map(e=>({id:e.id,name:e.name,date:e.date,key:norm(e.name),day:day(e.date)}));
 for(const e of eventRows){
  if(!e||typeof e!=='object')continue;
  const id=String(e.id??e.event_id??'');
  const name=e.name??e.title??e.event_name??null;
  const date=e.date??e.event_date??e.start_time??null;
  const key=id||norm(name)+'|'+String(date);
  if(ids.has(key)){duplicates.push(key);continue}ids.add(key);
  const nameMatches=citoEvents.filter(c=>c.key&&c.key===norm(name));
  const dated=nameMatches.filter(c=>day(date)&&c.day===day(date));
  const candidates=dated.length?dated:(!day(date)&&nameMatches.length===1?nameMatches:[]);
  const row={fighterapiId:id||null,name,date,source:'fighterapi',citoEventId:candidates.length===1?candidates[0].id:null,matchBasis:candidates.length===1?(dated.length?'name-and-date':'name-only-date-missing'):null};
  if(candidates.length===1)matched.push(row);else if(candidates.length>1||nameMatches.length>1&&!day(date))ambiguous.push(row);else unmatched.push(row);
 }
 const verifiedMatches=matched.filter(r=>r.matchBasis==='name-and-date');
 const provisionalMatches=matched.filter(r=>r.matchBasis!=='name-and-date');
 return {schemaVersion:1,source:'pfl-source-reconciliation',generatedAt:new Date().toISOString(),citoFighters:fighters.size,fighterapiAvailable:!!(api.schedule||api.events),fighterapiEvents:ids.size,matchedEvents:matched,verifiedMatches,provisionalMatches,unmatchedEvents:unmatched,ambiguousEvents:ambiguous,duplicateEventKeys:duplicates,oddsVerified:false,statLinesVerified:false,bettingReady:false};
}
if(require.main===module){
 const cito=JSON.parse(fs.readFileSync('data/pfl/events.json','utf8'));
 const api=fs.existsSync('data/pfl/fighterapi-snapshot.json')?JSON.parse(fs.readFileSync('data/pfl/fighterapi-snapshot.json','utf8')):{};
 const result=audit(cito,api);fs.writeFileSync('data/pfl/source-reconciliation.json',JSON.stringify(result,null,2)+'\n');
 console.log('PFL source reconciliation:',JSON.stringify({citoFighters:result.citoFighters,fighterapiEvents:result.fighterapiEvents,matched:result.matchedEvents.length,verified:result.verifiedMatches.length,provisional:result.provisionalMatches.length,unmatched:result.unmatchedEvents.length,ambiguous:result.ambiguousEvents.length,bettingReady:false}));
}
module.exports={audit,entries,norm};
