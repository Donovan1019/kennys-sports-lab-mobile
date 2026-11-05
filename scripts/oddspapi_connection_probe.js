/* Secret-safe OddsPapi account connectivity probe; request usage is provider-defined. */
'use strict';
const https=require('node:https');
function summarize(status,payload){
 const error=payload?.error||{};
 const code=typeof error.code==='string'?error.code.replace(/[^A-Za-z0-9_-]/g,'').slice(0,64):null;
 return {httpStatus:status,connected:status===200,providerErrorCode:code,hasResponseObject:!!payload&&typeof payload==='object'&&!Array.isArray(payload)};
}
function check(key){return new Promise((resolve,reject)=>{
 const url=new URL('https://api.oddspapi.io/v4/account');url.searchParams.set('apiKey',key);
 const req=https.get(url,{timeout:15000,headers:{Accept:'application/json'}},res=>{
 let body='';res.on('data',chunk=>{body+=chunk;if(body.length>200000)req.destroy(Error('oversized response'))});
 res.on('end',()=>{let parsed=null;try{parsed=JSON.parse(body)}catch{}resolve(summarize(res.statusCode,parsed))});
 });req.on('timeout',()=>req.destroy(Error('timeout')));req.on('error',reject);
})}
async function main(){
 const key=process.env.ODDSPAPI_API_KEY;
 if(!key){console.error('ODDSPAPI_PROBE '+JSON.stringify({connected:false,reason:'secret_missing'}));process.exitCode=1;return}
 try{const result=await check(key);console.log('ODDSPAPI_PROBE '+JSON.stringify(result));if(!result.connected)process.exitCode=1}
 catch(e){console.error('ODDSPAPI_PROBE '+JSON.stringify({connected:false,reason:'network_error'}));process.exitCode=1}
}
if(require.main===module)main();
module.exports={summarize};
