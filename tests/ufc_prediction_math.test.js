// Regression tests for analytical UFC Poisson count model.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('ufc_fighter_projections.js','utf8');
const start=source.indexOf('function poissonTail(lambda,threshold){');
const end=source.indexOf('\nfunction modeledProp(',start);
assert.ok(start>=0&&end>start,'Poisson implementation must exist');
const poissonTail=vm.runInNewContext('('+source.slice(start,end).trim()+')');
function near(actual,expected,tol=1e-8){assert.ok(Math.abs(actual-expected)<tol,`expected ${actual} ~ ${expected}`)}
near(poissonTail(1,0.5),1-Math.exp(-1));
near(poissonTail(2,1.5),1-3*Math.exp(-2));
near(poissonTail(0,0.5),0);
near(poissonTail(1000,999.5),0.5,0.03);
assert.equal(poissonTail(-1,0.5),null);
assert.equal(poissonTail(Number.NaN,0.5),null);
assert.ok(source.includes('Date.now()-Date.parse(q.updated_at)<=6*60*60*1000'),'reject stale individual quotes');
assert.ok(source.includes('Date.now()-Date.parse(book.fetched_at)<=6*60*60*1000'),'reject stale odds snapshots');
console.log('UFC probability math and quote-freshness tests passed');
