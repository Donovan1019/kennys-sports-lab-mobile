'use strict';
// One-shot opt-in provider capability probe; never publishes picks or logs credentials.
const https=require('node:https');
function get(path,key,params={}){
 return new Promise((resolve,reject)=>{
  const url=new URL('https://api.oddspapi.io/v4/'+path);
  url.searchParams.set('apiKey',key);
  for(const [k,v] of Object.entries(params))url.searchParams.set(k,String(v));
  const req=https.get(url,{timeout:20000,headers:{Accept:'application/json'}},res=>{
   let body='';res.on('data',x=>{body+=x;if(body.length>5e6)req.destroy(Error('response_too_large'))});
   res.on('end',()=>{let data=null;try{data=JSON.parse(body)}catch{}resolve({status:res.statusCode,data})});
  });req.on('timeout',()=>req.destroy(Error('timeout')));req.on('error',reject);
 });
}
function usage(payload){
 const sub=payload?.subscription||payload?.active_subscription||payload?.activeSubscription||payload;
 const limit=Number(sub?.request_limit),count=Number(sub?.request_count);
 return Number.isFinite(limit)&&Number.isFinite(count)?{limit,count,remaining:limit-count}:null;
}
async function main(){
 const key=process.env.ODDSPAPI_API_KEY;
 if(!key){console.log('ODDSPAPI_CAPABILITY '+JSON.stringify({status:'SECRET_MISSING'}));process.exitCode=1;return}
 try{
  const account=await get('account',key);
  if(account.status!==200){console.log('ODDSPAPI_CAPABILITY '+JSON.stringify({status:'AUTH_UNVERIFIED',httpStatus:account.status,errorCode:String(account.data?.error?.code||account.data?.code||'').replace(/[^A-Za-z0-9_-]/g,'').slice(0,50)}));process.exitCode=1;return}
  const u=usage(account.data);
  console.log('ODDSPAPI_ACCOUNT '+JSON.stringify({status:'AUTHENTICATED',usage:u}));
  if(process.env.ODDSPAPI_CAPABILITY_PROBE!=='true'){console.log('ODDSPAPI_CAPABILITY '+JSON.stringify({status:'BILLABLE_PROBE_DISABLED'}));return}
  if(!u||u.remaining<15){console.log('ODDSPAPI_CAPABILITY '+JSON.stringify({status:'BUDGET_GUARD',remaining:u?.remaining??null}));return}
  const books=await get('bookmakers',key);
  const slugs=Array.isArray(books.data)?books.data.map(x=>x?.bookmakerSlug||x?.slug||x?.bookmakerId).filter(Boolean):[];
  const hasPrizePicks=slugs.some(x=>String(x).toLowerCase()==='prizepicks');
  console.log('ODDSPAPI_BOOKMAKERS '+JSON.stringify({httpStatus:books.status,prizepicksListed:hasPrizePicks,bookmakersCount:slugs.length}));
  if(books.status!==200||!hasPrizePicks){process.exitCode=1;return}
  const markets=await get('markets',key);
  const props=Array.isArray(markets.data)?markets.data.filter(x=>x?.playerProp===true):[];
  console.log('ODDSPAPI_MARKETS '+JSON.stringify({httpStatus:markets.status,playerPropMarkets:props.length}));
  if(markets.status!==200||!props.length)process.exitCode=1;
 }catch{console.log('ODDSPAPI_CAPABILITY '+JSON.stringify({status:'NETWORK_OR_SCHEMA_ERROR'}));process.exitCode=1}
}
if(require.main===module)main();
module.exports={usage};
