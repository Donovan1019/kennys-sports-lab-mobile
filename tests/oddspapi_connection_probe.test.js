'use strict';
const assert=require('node:assert/strict');
const {summarize}=require('../scripts/oddspapi_connection_probe');
assert.deepEqual(summarize(200,{account:{apiKey:'SECRET'}}),{httpStatus:200,connected:true,providerErrorCode:null,hasResponseObject:true});
assert.deepEqual(summarize(429,{error:{code:'REQUEST_LIMIT_EXCEEDED'}}),{httpStatus:429,connected:false,providerErrorCode:'REQUEST_LIMIT_EXCEEDED',hasResponseObject:true});
assert.equal(JSON.stringify(summarize(200,{apiKey:'SECRET'})).includes('SECRET'),false);
console.log('OddsPapi secret-safe probe tests passed');
