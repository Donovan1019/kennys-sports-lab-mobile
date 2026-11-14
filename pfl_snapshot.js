/* PFL snapshot quality gate. Reject stale, unverified, or ambiguous event data. */
(function(root){'use strict';
function check(snapshot,now=Date.now()){
const errors=[];if(!snapshot||snapshot.schemaVersion!==1||!Array.isArray(snapshot.events))return {ok:false,errors:['Invalid snapshot schema'],events:[]};
const stamp=Date.parse(snapshot.retrievedAt);if(!Number.isFinite(stamp)||stamp>now+300000||now-stamp>24*3600000)errors.push('Snapshot missing, future-dated or older than 24 hours');
const ids=new Set(),events=[];
for(const e of snapshot.events){if(!e||typeof e.id!=='string'||!e.id.trim()||ids.has(e.id)){errors.push('Missing or duplicate event ID');continue}
ids.add(e.id);if(!e.name||!e.date||!Number.isFinite(Date.parse(e.date))){errors.push('Event '+e.id+' lacks verified name/date');continue}
events.push(e);
}
return {ok:errors.length===0,errors,events};
}
root.KSLPFLSnapshot=Object.freeze({check});
})(typeof window!=='undefined'?window:globalThis);
