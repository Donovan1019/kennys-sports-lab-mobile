const assert=require('node:assert/strict');
const {acquire,request}=require('../scripts/pfl_fighterapi_acquire');
(async()=>{
 const calls=[];
 const fetcher=async(url,options)=>{calls.push({url,options});return {ok:true,headers:{get:()=> '498'},json:async()=>({data:url.endsWith('/list_events')?{events:[{event_id:'600000001',status:'scheduled'}]}:{items:[]}})}};
 const result=await acquire('fake',fetcher);
 assert.equal(calls.length,3);assert.equal(result.league,'pfl');assert.equal(result.bettingReady,false);
 for(const call of calls){assert.equal(call.options.headers['x-api-key'],'fake');assert.equal(JSON.parse(call.options.body).league,'pfl')}
 assert.ok(result.schedule);assert.ok(result.events);assert.ok(result.odds);
 assert.equal(JSON.parse(calls[2].options.body).event_id,'600000001');
 const limited=await acquire('fake',async()=>({ok:false,status:402}));
 assert.equal(limited.errors.length,1);assert.equal(limited.events,null);
 await assert.rejects(()=>request('get_fighter',{},'fake',fetcher),/Unsupported/);
 console.log('FighterAPI PFL acquisition tests passed');
})().catch(error=>{console.error(error);process.exitCode=1});
