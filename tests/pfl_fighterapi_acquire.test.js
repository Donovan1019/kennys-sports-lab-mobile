const assert=require('node:assert/strict');
const {acquire,request}=require('../scripts/pfl_fighterapi_acquire');
(async()=>{
 const calls=[];
 const fetcher=async(url,options)=>{calls.push({url,options});return {ok:true,headers:{get:()=> '498'},json:async()=>({data:{items:[]}})}};
 const result=await acquire('fake',fetcher);
 assert.equal(calls.length,2);assert.equal(result.league,'pfl');assert.equal(result.bettingReady,false);
 for(const call of calls){assert.equal(call.options.headers['x-api-key'],'fake');assert.equal(JSON.parse(call.options.body).league,'pfl')}
 assert.ok(result.schedule);assert.ok(result.events);
 const limited=await acquire('fake',async()=>({ok:false,status:402}));
 assert.equal(limited.errors.length,1);assert.equal(limited.events,null);
 await assert.rejects(()=>request('get_fighter',{},'fake',fetcher),/Unsupported/);
 console.log('FighterAPI PFL acquisition tests passed');
})().catch(error=>{console.error(error);process.exitCode=1});
