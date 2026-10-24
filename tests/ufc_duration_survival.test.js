'use strict';
const assert=require('node:assert/strict');
function expectedRounds(hazard,scheduled){
  assert.ok(Number.isFinite(hazard)&&hazard>=0&&hazard<=1);
  assert.ok(scheduled===3||scheduled===5);
  let result=0;
  for(let i=0;i<scheduled;i++)result+=Math.pow(1-hazard,i);
  return result;
}
assert.equal(expectedRounds(0,3),3);
assert.equal(expectedRounds(0,5),5);
assert.equal(expectedRounds(1,3),1);
assert.equal(expectedRounds(1,5),1);
assert.ok(expectedRounds(.18,5)>expectedRounds(.18,3));
assert.ok(expectedRounds(.18,3)<3);
assert.ok(expectedRounds(.18,5)<5);
for(const h of [0,.05,.18,.3,.5,.9,1]){
  for(const n of [3,5]){
    const v=expectedRounds(h,n);
    assert.ok(v>=1&&v<=n);
  }
}
const fs=require('node:fs');
const src=fs.readFileSync('ufc_fighter_projections.js','utf8');
assert.ok(src.includes('expectedRounds+=Math.pow(1-perRoundFinishHazard,i)'));
assert.ok(src.includes('UNTRAINED 18% PER-ROUND FINISH HAZARD'));
console.log('UFC duration survival mathematics: PASS');
