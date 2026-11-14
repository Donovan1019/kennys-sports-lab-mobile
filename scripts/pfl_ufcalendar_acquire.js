#!/usr/bin/env node
/* Free-tier UFCalendar PFL acquisition. No secrets logged, no automatic paid upgrades. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const BASE='https://api.ufcalendar.com/v1';
async function request(endpoint,key,fetcher=fetch){
if(!key)throw Error('ufccal_key missing');
if(!/^\/events\?org=pfl(?:&[a-z_]+=[a-z0-9_-]+)*$/.test(endpoint))throw Error('Unsupported PFL endpoint');
const response=await fetcher(BASE+endpoint,{headers:{Authorization:'Bearer '+key,Accept:'application/json'},signal:AbortSignal.timeout(15000)});
if(!response.ok)throw Error('UFCalendar HTTP '+response.status);
const payload=await response.json();if(!Array.isArray(payload.data))throw Error('UFCalendar response missing event list');
return payload.data;
}
function normalizeEvent(e){if(!e||typeof e!=='object')return null;const slug=String(e.slug||'');const date=e.starts_at||null;
if(!slug||!e.title||!date||!Number.isFinite(Date.parse(date)))return null;
return {id:'ufcalendar:'+slug,slug,name:String(e.title),date,status:e.status||'unverified',source:'ufcalendar-pfl',bouts:[]};}
async function collect(key,fetcher=fetch){const data=await request('/events?org=pfl',key,fetcher);
return {schemaVersion:1,source:'ufcalendar-pfl',retrievedAt:new Date().toISOString(),dataScope:'event list only; bout odds and statistics not yet ingested',events:data.map(normalizeEvent).filter(Boolean)};}
async function main(){const data=await collect(process.env.ufccal_key);const dest=process.env.PFL_UFCAL_OUTPUT_PATH||'data/pfl/ufcalendar-events.json';fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(data,null,2)+'\n');console.log('Saved '+data.events.length+' UFCalendar PFL event metadata records');}
if(require.main===module)main().catch(e=>{console.error('UFCalendar PFL acquisition failed: '+e.message);process.exitCode=1});
module.exports={request,normalizeEvent,collect};
