#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
function assemble(readiness,odds){
 const bouts=new Map((readiness.bouts||[]).map(b=>[String(b.boutId),b]));
 const markets=[];
 for(const row of odds.accepted||[]){
  const bout=bouts.get(String(row.fightId));
  if(!bout?.identityAndHistoryVerified)continue;
  markets.push({fightId:row.fightId,selection:row.selection,market:row.market,book:row.book,odds:row.odds,oddsTimestamp:row.oddsTimestamp,bookVerified:true,boutVerified:true,fightStatus:'scheduled',line:row.line??null,side:row.side??null,settlementVerified:row.settlementVerified===true,modelCalibrated:false,simulationVerified:false,iterations:0,probability:null,bettingReady:false,blockedReasons:['MODEL_CALIBRATION_UNVERIFIED','MONTE_CARLO_UNVERIFIED']});
 }
 return {schemaVersion:1,source:'pfl-model-market-intake',generatedAt:new Date().toISOString(),markets,bettingReadyCount:0,reason:'Only verified markets are admitted; predictions require independently calibrated probabilities and simulations'};
}
if(require.main===module){
 const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));
 const out=assemble(load('data/pfl/bout-readiness.json'),load('data/pfl/odds-validation.json'));
 fs.writeFileSync('data/pfl/model-market-intake.json',JSON.stringify(out,null,2)+'\n');
 console.log('PFL model market intake:',JSON.stringify({verifiedMarkets:out.markets.length,bettingReady:out.bettingReadyCount}));
}
module.exports={assemble};
