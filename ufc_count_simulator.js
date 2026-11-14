(function(root){'use strict';
function hash(s){let h=2166136261;for(const c of String(s)){h=Math.imul(h^c.charCodeAt(0),16777619)}return h>>>0}
function rng(seed){let x=seed>>>0;return function(){x=(x+0x6D2B79F5)|0;let t=Math.imul(x^(x>>>15),1|x);t^=t+Math.imul(t^(t>>>7),61|t);return ((t^(t>>>14))>>>0)/4294967296}}
function poisson(lambda,random){if(!(lambda>=0)||!Number.isFinite(lambda))return null;if(lambda===0)return 0;const whole=Math.ceil(lambda/20),l=lambda/whole;let count=0;for(let k=0;k<whole;k++){let p=1,n=0;const limit=Math.exp(-l);do{p*=Math.max(1e-12,random());n++}while(p>limit);count+=n-1}return count}
function percentile(a,p){const i=Math.min(a.length-1,Math.floor(p*(a.length-1)));return a[i]}
function simulate(red,blue,rounds,opts={}){if(![3,5].includes(rounds))return {status:'MISSING_VERIFIED_ROUNDS'};const a=red?.career_round_totals,b=blue?.career_round_totals;if(!a||!b||![a.round_rows,b.round_rows].every(n=>Number.isFinite(n)&&n>0))return {status:'MISSING_FIGHTER_HISTORY'};
for(const t of [a,b])if(!['sig_landed','sig_attempted','td_landed','td_attempted'].every(k=>Number.isFinite(t[k])&&t[k]>=0)||t.sig_landed>t.sig_attempted||t.td_landed>t.td_attempted)return {status:'INVALID_STATS'};
const trials=Number.isInteger(opts.trials)&&opts.trials>=100&&opts.trials<=20000?opts.trials:4000;
const hazard=Number.isFinite(opts.hazard)?opts.hazard:0.16;if(hazard<0||hazard>1)return {status:'INVALID_HAZARD'};
const random=rng(hash((opts.seed||'UFC')+':'+rounds+':'+hazard));
const samples={redSig:[],blueSig:[],redTd:[],blueTd:[],duration:[]};let finishes=0;
for(let i=0;i<trials;i++){let duration=rounds;for(let r=1;r<=rounds;r++){if(random()<hazard){duration=r-1+random();finishes++;break}}samples.duration.push(duration);for(const [prefix,t] of [['red',a],['blue',b]]){samples[prefix+'Sig'].push(poisson(t.sig_landed/t.round_rows*duration,random));samples[prefix+'Td'].push(poisson(t.td_landed/t.round_rows*duration,random))}}
const summary={};for(const [key,arr] of Object.entries(samples)){arr.sort((a,b)=>a-b);summary[key]={median:percentile(arr,0.5),p10:percentile(arr,0.1),p90:percentile(arr,0.9),mean:arr.reduce((x,y)=>x+y,0)/trials}};
return {status:'HYPOTHETICAL_COUNT_SIMULATION',trials,rounds,hazard,finish_fraction:finishes/trials,summary,minimum_fighter_round_rows:Math.min(a.round_rows,b.round_rows),limitations:'Independent Poisson count draws and assumed per-round finish hazard. Partial rounds treated as full exposures. Not calibrated, opponent adjusted, or bet eligible.'}
}
root.KennyUfcCountSim={simulate};
})(typeof window!=='undefined'?window:globalThis);
