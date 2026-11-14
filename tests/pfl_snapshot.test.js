const assert=require('node:assert/strict');require('../pfl_snapshot.js');const C=globalThis.KSLPFLSnapshot;
const now=Date.parse('2026-11-14T12:00:00Z');const base={schemaVersion:1,retrievedAt:new Date(now).toISOString(),events:[{id:'e1',name:'PFL Event',date:'2026-11-20T19:00:00Z'}]};
assert.equal(C.check(base,now).ok,true);
assert.equal(C.check({...base,retrievedAt:'2020-01-01'},now).ok,false);
assert.equal(C.check({...base,events:[base.events[0],base.events[0]]},now).ok,false);
assert.equal(C.check({...base,events:[{id:'x',name:'Missing date'}]},now).ok,false);
console.log('PFL snapshot validation tests passed');
