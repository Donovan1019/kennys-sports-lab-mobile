#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path');
const BASE='https://mcp.fighterapi.com/v1/';
const ALLOWED=new Set(['list_events','get_schedule','get_event','get_odds']);
async function request(tool,params,key,fetcher=fetch){
 if(!ALLOWED.has(tool))throw Error('Unsupported FighterAPI endpoint');
 if(!key)throw Error('FIGHTERAPI_API_KEY missing');
 const response=await fetcher(BASE+tool,{method:'POST',headers:{'x-api-key':key,'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(params),signal:AbortSignal.timeout(20000)});
 if(!response.ok){const error=new Error('FighterAPI HTTP '+response.status);error.status=response.status;throw error}
 const json=await response.json();if(json.error)throw Error('FighterAPI returned an error');return {data:json.data??json,creditsRemaining:response.headers?.get?.('x-credits-remaining')??null};
}
async function acquire(key,fetcher=fetch){
 const snapshot={schemaVersion:1,source:'fighterapi',retrievedAt:new Date().toISOString(),league:'pfl',schedule:null,events:null,odds:null,errors:[],bettingReady:false};
 for(const [field,tool,params] of [['schedule','get_schedule',{league:'pfl'}],['events','list_events',{league:'pfl',status:'scheduled',limit:20}]]){
  try{const result=await request(tool,params,key,fetcher);snapshot[field]=result.data;snapshot.creditsRemaining=result.creditsRemaining}
  catch(error){snapshot.errors.push({field,status:error.status??null,message:error.message});if([401,402,429].includes(error.status))break}
 }
 if(snapshot.events||snapshot.schedule){
  try{const result=await request('get_odds',{league:'pfl'},key,fetcher);snapshot.odds=result.data;snapshot.oddsCreditsRemaining=result.creditsRemaining}
  catch(error){snapshot.errors.push({field:'odds',status:error.status??null,message:error.message});}
 }
 return snapshot;
}
async function main(){
 const key=process.env.FIGHTERAPI_API_KEY;if(!key){console.log('FighterAPI key not configured; skipping optional enrichment');return}
 const result=await acquire(key);const dest='data/pfl/fighterapi-snapshot.json';fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n');
 console.log('FighterAPI PFL snapshot: schedule='+!!result.schedule+', events='+!!result.events+', odds='+!!result.odds+', errors='+result.errors.length+', bettingReady=false');
 for(const issue of result.errors)console.warn('FighterAPI '+issue.field+' unavailable: HTTP '+(issue.status??'unknown')+'; '+String(issue.message).slice(0,180));
 if(result.errors.some(e=>e.field!=='odds'))process.exitCode=1;
}
if(require.main===module)main().catch(error=>{console.error(error.message);process.exitCode=1});
module.exports={request,acquire};
