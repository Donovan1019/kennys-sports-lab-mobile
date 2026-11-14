(function(){'use strict';
const el=id=>document.getElementById(id);
const defaults={strategy:'silver',legs:'3','parlay-market':'ml',stake:'25','target-odds':'200-300'};
let templates=[],intake=[];
const fmtOdds=n=>n>0?'+'+Math.round(n):String(Math.round(n));
function addLine(box,text,tag='p'){const node=document.createElement(tag);node.textContent=text;box.append(node);}
function verifiedPreview(stake,legs,strategy,market,min,max){
 if(!window.KSLPFLParlays||!window.KSLPFLBets)return null;
 const eligible=intake.filter(m=>window.KSLPFLBets.assess(m).eligible);
 if(eligible.length<legs)return null;
 const opts={stake,legs,strategy,market:market==='ml'?'ml':'totals',iterations:50000,seed:20261114,
  crossFightIndependenceValidated:eligible.every(m=>m.crossFightIndependenceValidated===true)};
 if(Number.isFinite(max)){opts.targetMinAmerican=min;opts.targetMaxAmerican=max}
 const result=window.KSLPFLParlays.build(eligible,opts);
 return result.eligible?result:null;
}
const ids=Object.keys(defaults);
function update(){const s=Number(el('stake').value);el('parlay-summary').textContent=el('legs').value+' legs · '+el('strategy').value.toUpperCase()+' · '+(Number.isFinite(s)&&s>0?'$'+s.toFixed(2):'Invalid stake')+' · target '+el('target-odds').value+' · '+templates.length+' reference templates · '+intake.length+' intake markets';}
function render(){
 const stake=Number(el('stake').value),legs=Number(el('legs').value),strategy=el('strategy').value,market=el('parlay-market').value;
 if(!Number.isFinite(stake)||stake<=0){el('parlay-result').textContent='Enter a positive stake.';return;}
 const target=el('target-odds').value;
 const [min,max]=target==='any'?[0,Infinity]:target.split('-').map(Number);
 const model=verifiedPreview(stake,legs,strategy,market,min,max);
 if(model){
  const box=el('parlay-result');box.replaceChildren();
  addLine(box,'INDEPENDENT MODEL — VERIFIED INPUTS','strong');
  const list=document.createElement('ol');
  for(const leg of model.legs){const li=document.createElement('li');li.textContent=leg.selection+' ('+fmtOdds(leg.odds)+') · Model '+(leg.probability*100).toFixed(1)+'% · Fair '+fmtOdds(leg.fairOdds)+' · EV '+(leg.individualEV*100).toFixed(1)+'%';list.append(li)}
  box.append(list);
  addLine(box,'Joint simulated win probability '+(model.modelProbability*100).toFixed(1)+'% · Combined '+fmtOdds((model.decimalOdds-1)*100)+' · Model EV '+(model.expectedValue*100).toFixed(1)+'%');
  addLine(box,'x.legs===legs&&x.strategy===strategy&&(x.market||'ml')===market&&
 Number.isFinite(x.referenceDecimalOdds)&&100*(x.referenceDecimalOdds-1)>=min&&100*(x.referenceDecimalOdds-1)<=max);
 if(!p){el('parlay-result').textContent='No fresh reference combination available for these settings. Market-intake records: '+intake.length+'. Independent model betting eligibility is not established. No market-reference ticket will be substituted outside the selected odds range.';return;}
 const box=el('parlay-result');box.replaceChildren();
 const title=document.createElement('strong');title.textContent='MARKET REFERENCE ONLY — NOT A BETTING RECOMMENDATION';box.append(title);
 const warning=document.createElement('p');warning.textContent=p.negativeEVWarning?'Negative reference EV. These prices do not establish a betting advantage.':'Reference prices are not sportsbook verified; no calibrated model or validated cross-fight correlation.';box.append(warning);
 const list=document.createElement('ol');for(const leg of p.markets){const li=document.createElement('li');li.textContent=leg.selection+' ('+(leg.american>0?'+':'')+leg.american+')';list.append(li);}box.append(list);
 const info=document.createElement('p');info.textContent=p.iterations.toLocaleString()+' market-implied draws · Combined reference decimal '+p.referenceDecimalOdds.toFixed(2)+' · $'+stake.toFixed(2)+' stake → $'+(stake*(p.referenceDecimalOdds-1)).toFixed(2)+' reference profit · Reference EV '+(p.referenceEV*100).toFixed(1)+'%';box.append(info);
 const metrics=document.createElement('p');metrics.textContent='Independent model probability: UNAVAILABLE · Model fair odds: UNAVAILABLE · Model EV: UNAVAILABLE · Calibration: UNVERIFIED · Betting status: PASS';box.append(metrics);
}
ids.forEach(id=>el(id).addEventListener('input',update));
el('generate-parlay').addEventListener('click',render);
el('reset-parlay').addEventListener('click',()=>{for(const id of ids)el(id).value=defaults[id];update();el('parlay-result').textContent='Choose settings and generate a market-reference combination.';});
Promise.all([window.KSLPFLFeed.load(),fetch('./data/pfl/parlay-candidates.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).catch(()=>null)]).then(([feed,data])=>{intake=feed.markets||[];const now=Date.now();templates=(data?.parlays||[]).filter(p=>p.markets?.every(m=>Number.isFinite(Date.parse(m.recordedAt))&&now-Date.parse(m.recordedAt)>=-300000&&now-Date.parse(m.recordedAt)<=7200000));el('parlay-result').textContent=templates.length?'Ready: '+templates.length+' fresh reference combinations. Select settings and generate.':'No fresh parlay combinations available. Await the next published odds snapshot.';update();}).catch(e=>{el('parlay-result').textContent='Parlay feed unavailable: '+e.message;});update();
})();+stake.toFixed(2)+' stake · x.legs===legs&&x.strategy===strategy&&(x.market||'ml')===market&&
 Number.isFinite(x.referenceDecimalOdds)&&100*(x.referenceDecimalOdds-1)>=min&&100*(x.referenceDecimalOdds-1)<=max);
 if(!p){el('parlay-result').textContent='No fresh reference combination available for these settings. Verified betting markets remain '+intake.length+'. No market-reference ticket will be substituted outside the selected odds range.';return;}
 const box=el('parlay-result');box.replaceChildren();
 const title=document.createElement('strong');title.textContent='MARKET REFERENCE ONLY — NOT A BETTING RECOMMENDATION';box.append(title);
 const warning=document.createElement('p');warning.textContent=p.negativeEVWarning?'Negative reference EV. These prices do not establish a betting advantage.':'Reference prices are not sportsbook verified; no calibrated model or validated cross-fight correlation.';box.append(warning);
 const list=document.createElement('ol');for(const leg of p.markets){const li=document.createElement('li');li.textContent=leg.selection+' ('+(leg.american>0?'+':'')+leg.american+')';list.append(li);}box.append(list);
 const info=document.createElement('p');info.textContent=p.iterations.toLocaleString()+' market-implied draws · Combined reference decimal '+p.referenceDecimalOdds.toFixed(2)+' · $'+stake.toFixed(2)+' stake → $'+(stake*(p.referenceDecimalOdds-1)).toFixed(2)+' reference profit · Reference EV '+(p.referenceEV*100).toFixed(1)+'%';box.append(info);
 const metrics=document.createElement('p');metrics.textContent='Independent model probability: UNAVAILABLE · Model fair odds: UNAVAILABLE · Model EV: UNAVAILABLE · Calibration: UNVERIFIED · Betting status: PASS';box.append(metrics);
}
ids.forEach(id=>el(id).addEventListener('input',update));
el('generate-parlay').addEventListener('click',render);
el('reset-parlay').addEventListener('click',()=>{for(const id of ids)el(id).value=defaults[id];update();el('parlay-result').textContent='Choose settings and generate a market-reference combination.';});
Promise.all([window.KSLPFLFeed.load(),fetch('./data/pfl/parlay-candidates.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).catch(()=>null)]).then(([feed,data])=>{intake=feed.markets||[];const now=Date.now();templates=(data?.parlays||[]).filter(p=>p.markets?.every(m=>Number.isFinite(Date.parse(m.recordedAt))&&now-Date.parse(m.recordedAt)>=-300000&&now-Date.parse(m.recordedAt)<=7200000));el('parlay-result').textContent=templates.length?'Ready: '+templates.length+' fresh reference combinations. Select settings and generate.':'No fresh parlay combinations available. Await the next published odds snapshot.';update();}).catch(e=>{el('parlay-result').textContent='Parlay feed unavailable: '+e.message;});update();
})();+model.netProfit.toFixed(2)+' possible profit · '+model.iterations.toLocaleString()+' model draws');
  return;
 }
 const p=templates.find(x=>x.legs===legs&&x.strategy===strategy&&(x.market||'ml')===market&&
 Number.isFinite(x.referenceDecimalOdds)&&100*(x.referenceDecimalOdds-1)>=min&&100*(x.referenceDecimalOdds-1)<=max);
 if(!p){el('parlay-result').textContent='No fresh reference combination available for these settings. Verified betting markets remain '+intake.length+'. No market-reference ticket will be substituted outside the selected odds range.';return;}
 const box=el('parlay-result');box.replaceChildren();
 const title=document.createElement('strong');title.textContent='MARKET REFERENCE ONLY — NOT A BETTING RECOMMENDATION';box.append(title);
 const warning=document.createElement('p');warning.textContent=p.negativeEVWarning?'Negative reference EV. These prices do not establish a betting advantage.':'Reference prices are not sportsbook verified; no calibrated model or validated cross-fight correlation.';box.append(warning);
 const list=document.createElement('ol');for(const leg of p.markets){const li=document.createElement('li');li.textContent=leg.selection+' ('+(leg.american>0?'+':'')+leg.american+')';list.append(li);}box.append(list);
 const info=document.createElement('p');info.textContent=p.iterations.toLocaleString()+' market-implied draws · Combined reference decimal '+p.referenceDecimalOdds.toFixed(2)+' · $'+stake.toFixed(2)+' stake → $'+(stake*(p.referenceDecimalOdds-1)).toFixed(2)+' reference profit · Reference EV '+(p.referenceEV*100).toFixed(1)+'%';box.append(info);
 const metrics=document.createElement('p');metrics.textContent='Independent model probability: UNAVAILABLE · Model fair odds: UNAVAILABLE · Model EV: UNAVAILABLE · Calibration: UNVERIFIED · Betting status: PASS';box.append(metrics);
}
ids.forEach(id=>el(id).addEventListener('input',update));
el('generate-parlay').addEventListener('click',render);
el('reset-parlay').addEventListener('click',()=>{for(const id of ids)el(id).value=defaults[id];update();el('parlay-result').textContent='Choose settings and generate a market-reference combination.';});
Promise.all([window.KSLPFLFeed.load(),fetch('./data/pfl/parlay-candidates.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).catch(()=>null)]).then(([feed,data])=>{intake=feed.markets||[];const now=Date.now();templates=(data?.parlays||[]).filter(p=>p.markets?.every(m=>Number.isFinite(Date.parse(m.recordedAt))&&now-Date.parse(m.recordedAt)>=-300000&&now-Date.parse(m.recordedAt)<=7200000));el('parlay-result').textContent=templates.length?'Ready: '+templates.length+' fresh reference combinations. Select settings and generate.':'No fresh parlay combinations available. Await the next published odds snapshot.';update();}).catch(e=>{el('parlay-result').textContent='Parlay feed unavailable: '+e.message;});update();
})();