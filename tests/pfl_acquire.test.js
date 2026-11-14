const assert=require('node:assert/strict');const P=require('../scripts/pfl_acquire.js');
assert.equal(P.normalizeBout({id:'b1',scheduledRounds:3,fighters:[{fighterSlug:'x'}]}).strikeStats,null);
assert.equal(P.normalizeBout({id:'b1',scheduledRounds:3,fighters:[{fighterSlug:'x'}]}).fighters[0].slug,'x');
assert.equal(P.normalizeEvent({slug:'abc',name:'Event'}).id,'abc');
const fetcher=async(url,opts)=>({ok:true,json:async()=>({success:true,data:url.endsWith('/upcoming')||url.endsWith('/recent')?[{slug:url.endsWith('/upcoming')?'future':'past',name:'PFL',date:'2026-11-14'}]:{slug:'future',card:[{id:'b1',scheduledRounds:3,fighters:[{fighterSlug:'x',fighterName:'Fighter X'}]}]}})});
P.collect('test-key',fetcher).then(x=>{assert.equal(x.events.length,2);assert.equal(x.source,'cito-pfl');assert.equal(x.events[0].bouts.length,1);console.log('PFL acquisition tests passed')}).catch(e=>{console.error(e);process.exitCode=1});
