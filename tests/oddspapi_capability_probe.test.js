'use strict';
const assert=require('node:assert/strict');
const {usage}=require('../scripts/oddspapi_capability_probe');
assert.deepEqual(usage({request_limit:250,request_count:10}),{limit:250,count:10,remaining:240});
assert.deepEqual(usage({subscription:{request_limit:250,request_count:0}}),{limit:250,count:0,remaining:250});
assert.equal(usage({}),null);
console.log('OddsPapi quota guard tests passed');
