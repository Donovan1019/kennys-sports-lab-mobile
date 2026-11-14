const assert=require('node:assert/strict');const P=require('../scripts/pfl_acquire.js');
assert.equal(P.normalizeBout({id:'b1',scheduledRounds:3,fighters:[{fighterSlug:'x'}]}).strikeStats,null);
assert.equal(P.normalizeBout({id:'b1',scheduledRounds:3,fighters:[{fighterSlug:'x'}]}).fighters[0].slug,'x');
assert.equal(P.normalizeEvent({slug:'abc',name:'Event'}).id,'abc');
const fetcher=async(url,opts)=>({ok:true,json:async()=>({success:true,data:[{slug:url.includes('upcoming')?'future':'past',name:'PFL'}]})});
P.collect('test-key',fetcher).then(x=>{assert.equal(x.events.length,2);assert.equal(x.source,'cito-pfl');console.log('PFL acquisition tests passed')}).catch(e=>{console.error(e);process.exitCode=1});
