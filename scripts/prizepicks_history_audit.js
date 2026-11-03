/* Auditable historical-source readiness; no invented source connections. */
'use strict';
const {joinHistory}=require('./prizepicks_history_join');
function auditHistory(feed,records,now=Date.now()){
 const joined=joinHistory(feed,records,now);
 if(joined.status!=='HISTORICAL_RESEARCH_ONLY')return {status:'UNAVAILABLE',reason:joined.reason,coverage:{total:0,matched:0,unavailable:0},rows:[]};
 const matched=joined.rows.filter(r=>r.history.status==='HISTORICAL_ONLY').length;
 return {status:matched?'PARTIAL_HISTORY':'UNAVAILABLE',generated_at:joined.generated_at,coverage:{total:joined.rows.length,matched,unavailable:joined.rows.length-matched},rows:joined.rows.map(r=>({id:r.id,league:r.league,player:r.player,market:r.market,line:r.line,historyStatus:r.history.status,reason:r.history.reason||null,sample:r.history.sample||0,moreRate:r.history.status==='HISTORICAL_ONLY'?r.history.moreRate:null,lessRate:r.history.status==='HISTORICAL_ONLY'?r.history.lessRate:null,last5:r.history.status==='HISTORICAL_ONLY'?r.history.last5:null,last10:r.history.status==='HISTORICAL_ONLY'?r.history.last10:null,last15:r.history.status==='HISTORICAL_ONLY'?r.history.last15:null,modelValidated:false,betEligible:false}))};
}
module.exports={auditHistory};
