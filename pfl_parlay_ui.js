(function(){'use strict';
const el=id=>document.getElementById(id);
const defaults={strategy:'silver',legs:'3',market:'ml',stake:'25'};
let templates=[],verified=[];
const ids=Object.keys(defaults);
function update(){const s=Number(el('stake').value);el('parlay-summary').textContent=el('legs').value+' legs · '+el('strategy').value.toUpperCase()+' · '+(Number.isFinite(s)&&s>0?'$'+s.toFixed(2):'Invalid stake')+' · '+templates.length+' reference templates · '+verified.length+' verified markets';}
function render(){
 const stake=Number(el('stake').value),legs=Number(el('legs').value),strategy=el('strategy').value,market=el('market').value;
 if(!Number.isFinite(stake)||stake<=0){el('parlay-result').textContent='Enter a positive stake.';return;}
 if(market==='totals'){el('parlay-result').textContent='No independently validated total-round parlay combinations available.';return;}
 const p=templates.find(x=>x.legs===legs&&x.strategy===strategy);
 if(!p){el('parlay-result').textContent='No fresh reference combination available for these settings. Verified betting markets remain '+verified.length+'.';return;}
 const box=el('parlay-result');box.replaceChildren();
 const title=document.createElement('strong');title.textContent='MARKET REFERENCE ONLY — NOT A BETTING RECOMMENDATION';box.append(title);
 const warning=document.createElement('p');warning.textContent=p.negativeEVWarning?'Negative reference EV. These prices do not establish a betting advantage.':'Reference prices are not sportsbook verified; no calibrated model or validated cross-fight correlation.';box.append(warning);
 const list=document.createElement('ol');for(const leg of p.markets){const li=document.createElement('li');li.textContent=leg.selection+' ('+(leg.american>0?'+':'')+leg.american+')';list.append(li);}box.append(list);
 const info=document.createElement('p');info.textContent=p.iterations.toLocaleString()+' market-implied draws · Combined reference decimal '+p.referenceDecimalOdds.toFixed(2)+' · $'+stake.toFixed(2)+' stake → $'+(stake*(p.referenceDecimalOdds-1)).toFixed(2)+' reference profit · Reference EV '+(p.referenceEV*100).toFixed(1)+'%';box.append(info);
}
ids.forEach(id=>el(id).addEventListener('input',update));
el('generate-parlay').addEventListener('click',render);
el('reset-parlay').addEventListener('click',()=>{for(const id of ids)el(id).value=defaults[id];update();el('parlay-result').textContent='Choose settings and generate a market-reference combination.';});
Promise.all([window.KSLPFLFeed.load(),fetch('./data/pfl/parlay-candidates.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).catch(()=>null)]).then(([feed,data])=>{verified=feed.markets||[];const now=Date.now();templates=(data?.parlays||[]).filter(p=>p.markets?.every(m=>Number.isFinite(Date.parse(m.recordedAt))&&now-Date.parse(m.recordedAt)>=-300000&&now-Date.parse(m.recordedAt)<=7200000));el('parlay-result').textContent=templates.length?'Ready: '+templates.length+' fresh reference combinations. Select settings and generate.':'No fresh parlay combinations available. Await the next published odds snapshot.';update();}).catch(e=>{el('parlay-result').textContent='Parlay feed unavailable: '+e.message;});update();
})();