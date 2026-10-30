(()=>{'use strict';
const root=document.getElementById('ksl-ufc-projection');if(!root)return;
const markets=['Moneyline','KO/TKO win','Submission win','Decision win','Disqualification win','Fight goes distance','Fight ends inside distance','Total rounds','Alternate rounds','Round 1 winner','Round 2 winner','Round 3 winner','Round 4 winner','Round 5 winner','Exact finish round','Method and round','Double chance','Significant strikes landed','Significant strikes attempted','Total strikes landed','Takedowns landed','Takedowns attempted','Submission attempts','Knockdowns','Control time','Combined significant strikes','Combined takedowns','Round-specific strikes','Round-specific takedowns','Fight duration','Starts round 2/3/4/5','Reaches end of round','First 60/90/120 seconds finish','Live moneyline','Live round totals','Event parlay / SGP','Alternate fighter props'];
const h=document.createElement('h2');h.textContent='📈 Fighter Projections · Model Estimates';root.append(h);
const p=document.createElement('p');p.textContent='Scheduled UFC matchup research. Every supported market can be selected. Numerical projections, probability, sportsbook lines and EV are unavailable without validated fighter inputs and verified odds. Historical records alone do not establish fight readiness.';root.append(p);
const controls=document.createElement('div');controls.className='ksl-ufc-controls';root.append(controls);
const market=document.createElement('select'),bout=document.createElement('select');market.setAttribute('aria-label','UFC projection market');bout.setAttribute('aria-label','UFC matchup');for(const m of markets){const o=document.createElement('option');o.value=m;o.textContent=m;market.append(o)}const all=document.createElement('option');all.value='';all.textContent='All upcoming matchups';bout.append(all);controls.append(market,bout);market.value='Significant strikes landed';
const count=document.createElement('p');count.setAttribute('role','status');root.append(count);
const wrap=document.createElement('div');wrap.className='ksl-ufc-table-wrap';const table=document.createElement('table');const thead=document.createElement('thead');const tr=document.createElement('tr');for(const name of ['Fighter','Opponent','Start ET','Market','Model / baseline','DK / FD','Market %','Status']){const th=document.createElement('th');th.textContent=name;tr.append(th)}thead.append(tr);table.append(thead);const tbody=document.createElement('tbody');table.append(tbody);wrap.append(table);root.append(wrap);const cards=document.createElement('div');cards.className='ksl-ufc-projection-cards';root.append(cards);
let fights=[],eloById=new Map(),statsByName=new Map(),profileByName=new Map(),odds=[],oddsFetched=null;
const norm=s=>String(s||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9 ]/g,'').replace(/\s+/g,' ').trim();
function eastern(s){const d=new Date(s);return Number.isFinite(d.getTime())?d.toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}):'UNVERIFIED'}
const fmt=p=>Number.isFinite(p)&&(p<=-100||p>=100)?(p>0?'+':'')+p:'—';
const validQuote=q=>q&&['draftkings','fanduel'].includes(q.bookmaker)&&Number.isFinite(q.price)&&(q.price<=-100||q.price>=100)&&Number.isFinite(Date.parse(q.commence_time))&&Date.parse(q.commence_time)>Date.now()&&Number.isFinite(Date.parse(q.updated_at))&&Date.parse(q.updated_at)<=Date.now()&&Date.now()-Date.parse(q.updated_at)<=6*60*60*1000&&Number.isFinite(Date.parse(oddsFetched))&&Date.parse(oddsFetched)<=Date.now()&&Date.now()-Date.parse(oddsFetched)<=6*60*60*1000&&Date.parse(q.updated_at)<=Date.parse(oddsFetched)&&Date.parse(oddsFetched)<Date.parse(q.commence_time)&&!!q.event_id;
function implied(a){return a<0?(-a)/((-a)+100):100/(a+100)}
function quoteGroup(f,book){const target=[norm(f.red),norm(f.blue)];return odds.filter(q=>{if(q.market!=='h2h'||q.bookmaker!==book||!validQuote(q)||!target.includes(norm(q.selection)))return false;const sides=String(q.event||'').split(/\s+@\s+|\s+vs\.?\s+|\s+v\.?\s+/i).map(norm);return sides.length===2&&sides.every(n=>target.includes(n))&&sides[0]!==sides[1]&&Math.abs(Date.parse(q.commence_time)-Date.parse(f.start_time))<=90*60*1000;});}
function marketBaseline(f,fighter){const results=[];for(const book of ['draftkings','fanduel']){const rows=quoteGroup(f,book),a=rows.find(q=>norm(q.selection)===norm(fighter)),other=rows.find(q=>norm(q.selection)===norm(fighter===f.red?f.blue:f.red));if(a&&other&&a.event_id===other.event_id&&a.event===other.event&&a.commence_time===other.commence_time&&norm(a.selection)!==norm(other.selection)&&Math.abs(Date.parse(a.updated_at)-Date.parse(other.updated_at))<=15*60*1000){const p=implied(a.price),q=implied(other.price);const total=p+q;if(total>=1&&total<=1.35)results.push({book,price:a.price,novig:p/(p+q),timestamp:a.updated_at})}}return results}
function expectedValue(probability,americanOdds){if(!Number.isFinite(probability)||probability<0||probability>1||!Number.isFinite(americanOdds)||(americanOdds>-100&&americanOdds<100))return null;const profit=americanOdds>0?americanOdds/100:100/(-americanOdds);return probability*profit-(1-probability)}
function fairAmerican(p){if(!Number.isFinite(p)||p<=0||p>=1)return '—';return p>=0.5?'-'+Math.round(100*p/(1-p)):'+'+Math.round(100*(1-p)/p)}
function missingModelReason(f){const names=[f.red,f.blue];const missing=names.filter(n=>{const p=profileByName.get(norm(n));return !p||p.status!=='MATCHED_HISTORICAL_STATS'||!p.career_round_totals||!(p.career_round_totals.round_rows>0)||!Number.isFinite(p.career_round_totals.sig_landed)});if(missing.length)return 'UNAVAILABLE: '+missing.join(', ')+' missing verified historical striking rounds';const elo=eloById.get(String(f.id));if(elo&&elo.status==='INSUFFICIENT_MATCHED_HISTORY')return 'UNAVAILABLE: insufficient matched historical bouts';return 'UNAVAILABLE: independent model inputs incomplete'}
function quoteComparison(f,fighter){const prices=marketBaseline(f,fighter);if(!prices.length)return {market:'No verified two-sided market',fair:'—',ev:'—',model:'—'};const marketP=prices.reduce((n,q)=>n+q.novig,0)/prices.length;const marketFair=fairAmerican(marketP);const estimate=independentWinEstimate(f,fighter);const quote=prices.map(q=>q.book.toUpperCase()+' '+fmt(q.price)).join(' · ');if(!estimate)return {market:(marketP*100).toFixed(1)+'% · '+quote,fair:'Market '+marketFair,ev:'EV formula ready · probability estimate missing',model:missingModelReason(f)};const modelP=estimate.probability;const values=prices.map(q=>{return {book:q.book,ev:expectedValue(modelP,q.price)}});return {market:(marketP*100).toFixed(1)+'% · '+quote,fair:'Market '+marketFair+(estimate.rounds===0?' · Model fair odds UNAVAILABLE (neutral prior)':' · Heuristic '+fairAmerican(modelP)),ev:values.map(v=>v.book.toUpperCase()+' '+(v.ev>=0?'+':'')+(v.ev*100).toFixed(1)+'%').join(' · ')+(estimate.rounds===0?' (NEUTRAL PRIOR SCENARIO · NOT AN EDGE)':' (UNCALIBRATED · NOT A BET)'),model:(modelP*100).toFixed(1)+'% · '+(estimate.rounds===0?'neutral 50/50 prior, NOT a prediction':'uncalibrated research estimate')};}
function bookPrices(f,fighter){const results=marketBaseline(f,fighter);return ['draftkings','fanduel'].map(book=>{const x=results.find(v=>v.book===book);return x?fmt(x.price):'—'}).join(' / ')}
// Transparent first-pass research heuristic. NOT a trained/calibrated probability model.
function careerRate(s,k){const t=s?.career_round_totals;return t&&t.round_rows>0&&Number.isFinite(t[k])?t[k]/t.round_rows:null}
function independentWinEstimate(f,fighter){
  const self=statsByName.get(norm(fighter)),opp=statsByName.get(norm(fighter===f.red?f.blue:f.red));
  const sr=careerRate(self,'sig_landed'),or=careerRate(opp,'sig_landed'),st=careerRate(self,'td_landed'),ot=careerRate(opp,'td_landed');
  // Partial-data prior: unavailable fighter rates revert to neutral, not to invented stats.
  // No history on either side yields exactly 50/50, not a claimed edge.
  const knownRounds=Math.min(self?.career_round_totals?.round_rows||0,opp?.career_round_totals?.round_rows||0);
  const rawElo=eloById.get(String(f.id));const es=rawElo&&norm(rawElo.red)===norm(f.red)&&norm(rawElo.blue)===norm(f.blue)&&Date.parse(rawElo.start_time)===Date.parse(f.start_time)?rawElo:null;
  const selfElo=es?(fighter===f.red?es.red_elo:es.blue_elo):null;
  const oppElo=es?(fighter===f.red?es.blue_elo:es.red_elo):null;
  const eloTerm=Number.isFinite(selfElo)&&Number.isFinite(oppElo)?Math.max(-0.65,Math.min(0.65,(selfElo-oppElo)/500)):0;
  // Regularized, bounded, symmetric score: strike rate + takedown rate + available Elo.
  const strikeTerm=Math.max(-0.5,Math.min(0.5,Math.log(((sr??3)+3)/((or??3)+3))*0.45));
  const takedownTerm=Math.max(-0.3,Math.min(0.3,Math.log(((st??0)+0.5)/((ot??0)+0.5))*0.18));
  const n=knownRounds;
  const weight=n/(n+24); // conservative shrinkage for sparse histories; not fitted
  const score=weight*(eloTerm+strikeTerm+takedownTerm);
  const probability=1/(1+Math.exp(-score));
  return {probability,source:n===0?'NEUTRAL PRIOR — NO INDEPENDENT FIGHTER EVIDENCE':'UNCALIBRATED SHRUNK HEURISTIC',rounds:n,weight};
}
function researchProjection(f,fighter,stat){
  const opponent=statsByName.get(norm(fighter===f.red?f.blue:f.red));
  const m={'Significant strikes landed':'sig_landed','Significant strikes attempted':'sig_attempted','Total strikes landed':'total_landed','Takedowns landed':'td_landed','Takedowns attempted':'td_attempted','Submission attempts':'submission_attempts','Knockdowns':'knockdowns','Control time':'control_seconds'}[market.value];
  if(!m)return null;
  const own=careerRate(stat,m);if(own===null)return null;
  // 3-round equivalent rather than assuming the bout is scheduled for three rounds.
  // Opponent exposure is not available in the current mirror, so shrink to neutral league-style
  // conservative adjustment of 1.0, not a fabricated opponent defensive figure.
  const scheduled=f.scheduled_rounds===5?5:f.scheduled_rounds===3?3:null;
  const horizon=scheduled??3;
  // Exploratory survival baseline, not a trained finish model: at a constant
  // per-round finish hazard, expected active rounds is the sum of survival
  // probabilities for each scheduled round.
  const perRoundFinishHazard=0.18;
  let expectedRounds=0;
  for(let i=0;i<horizon;i++)expectedRounds+=Math.pow(1-perRoundFinishHazard,i);
  return {value:own*expectedRounds,units:m==='control_seconds'?'sec expected':'expected',rounds:stat.career_round_totals.round_rows,scheduledVerified:scheduled!==null,expectedRounds,horizon,assumption:'UNTRAINED 18% PER-ROUND FINISH HAZARD'};
}
// Transparent analytical distribution for count props; NOT a calibrated betting model.
function poissonTail(lambda,threshold){
 if(!Number.isFinite(lambda)||lambda<0||lambda>10000||!Number.isFinite(threshold))return null;
 const k=Math.floor(threshold);if(k<0)return 1;
 // For large lambda use a continuity-corrected normal approximation to avoid underflow.
 if(lambda>600){const z=(k+0.5-lambda)/Math.sqrt(lambda);const t=1/(1+0.2316419*Math.abs(z));const d=0.3989422804014327*Math.exp(-z*z/2);const c=1-d*t*(0.319381530+t*(-0.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))));return Math.max(0,Math.min(1,z>=0?1-c:c));}
 let term=Math.exp(-lambda),cdf=term;
 for(let i=1;i<=k;i++){term*=lambda/i;cdf+=term}
 return Math.max(0,Math.min(1,1-cdf));
}
function modeledProp(f,fighter,stat){
 const projection=researchProjection(f,fighter,stat);
 if(!projection)return null;
 const countMarkets=['Significant strikes landed','Significant strikes attempted','Total strikes landed','Takedowns landed','Takedowns attempted','Submission attempts','Knockdowns'];
 if(!countMarkets.includes(market.value))return {...projection,distribution:'NO COUNT DISTRIBUTION'};
 return {...projection,distribution:'POISSON RESEARCH BASELINE',overAtHalf:poissonTail(projection.value,Math.floor(projection.value)+0.5)};
}
function modelDisplay(f,fighter,stat){
if(market.value==='Moneyline'){
  const independent=independentWinEstimate(f,fighter);
  return independent?(independent.probability*100).toFixed(1)+'% · '+(independent.rounds===0?'NEUTRAL PRIOR, no fighter evidence':'uncalibrated research estimate'):missingModelReason(f);
}
const projected=modeledProp(f,fighter,stat);
return projected?projected.value.toFixed(1)+' '+projected.units+' ('+projected.expectedRounds.toFixed(2)+' expected rounds / '+projected.horizon+' scheduled; illustrative finish hazard 18% per round)' +(projected.scheduledVerified?'':' · schedule unverified')+(projected.distribution==='POISSON RESEARCH BASELINE'?' · exploratory count model · P(>'+Math.floor(projected.value)+'.5) '+(projected.overAtHalf*100).toFixed(1)+'%':''):'NO MATCHED STAT SAMPLE';
}
function rateLeader(f,key){
 const a=careerRate(statsByName.get(norm(f.red)),key),b=careerRate(statsByName.get(norm(f.blue)),key);
 if(a===null||b===null)return {name:'Insufficient comparable history',detail:'Historical rates only'};
 const pick=Math.abs(a-b)<0.0001?'Tied':a>b?f.red:f.blue;
 return {name:pick,detail:f.red+' '+a.toFixed(2)+' vs '+f.blue+' '+b.toFixed(2)+' per recorded round'};
}
function boutAssessment(f){
 const a=independentWinEstimate(f,f.red),b=independentWinEstimate(f,f.blue);
 const qa=marketBaseline(f,f.red),qb=marketBaseline(f,f.blue);
 const marketA=qa.length?qa.reduce((n,x)=>n+x.novig,0)/qa.length:null;
 const modelPick=a&&b&&a.rounds>0&&b.rounds>0&&Math.abs(a.probability-b.probability)>0.001?(a.probability>=b.probability?f.red:f.blue):null;
 const marketPick=marketA===null?null:marketA>=0.5?f.red:f.blue;
 const modelPct=a&&b?Math.max(a.probability,b.probability)*100:null;
 const marketPct=marketA===null?null:Math.max(marketA,1-marketA)*100;
 // A lean is not a bet. No positive EV claim without a calibrated, independently validated model.
 const decision=modelPick?'RESEARCH LEAN · '+modelPick:marketPick?'MARKET FAVORITE · '+marketPick:'NO RELIABLE PICK';
 const basis=modelPick?'Uncalibrated fighter-stat model · '+modelPct.toFixed(1)+'%':marketPick?'Bookmaker consensus · '+marketPct.toFixed(1)+'% no-vig · neutral model prior where history is missing':'Neutral 50/50 research prior · no reliable fighter history or sportsbook data';
 return {decision,basis,modelPick,marketPick,marketPct,strikes:rateLeader(f,'sig_landed'),takedowns:rateLeader(f,'td_landed')};
}
function render(){
 tbody.replaceChildren();cards.replaceChildren();
 const chosen=fights.filter(f=>!bout.value||String(f.id)===bout.value);
 let matched=0,priced=0;
 const add=(parent,label,value)=>{const line=document.createElement('div');line.className='ksl-ufc-projection-field';const k=document.createElement('span');k.textContent=label;const v=document.createElement('strong');v.textContent=value;line.append(k,v);parent.append(line)};
 for(const f of chosen){
   const assess=boutAssessment(f),card=document.createElement('article');card.className='ksl-ufc-projection-card';
   const title=document.createElement('h3');title.textContent=f.red+' vs '+f.blue;card.append(title);
   add(card,'Start ET',eastern(f.start_time));
   add(card,'Research assessment',assess.modelPick?assess.decision:'Independent winner prediction: insufficient matched fighter history');
   add(card,'Market favorite (not model)',assess.marketPick?assess.marketPick+' · '+assess.marketPct.toFixed(1)+'% no-vig':'No fresh complete two-sided quote');
   const detail=document.createElement('details');detail.className='ufc-fight-evidence';const summary=document.createElement('summary');summary.textContent='Expand model evidence, sportsbook odds and audit';detail.append(summary);card.append(detail);
   add(detail,'Fight status',Date.parse(f.start_time)<=Date.now()?'Start time passed · live/result UNVERIFIED':'Scheduled · not yet started by listed time');
   add(detail,'Prediction basis',assess.basis);
   add(detail,'Striking leader',assess.strikes.name);add(detail,'Striking comparison',assess.strikes.detail);
   add(detail,'Takedown leader',assess.takedowns.name);add(detail,'Takedown comparison',assess.takedowns.detail);
   for(const fighter of [f.red,f.blue]){const comparison=quoteComparison(f,fighter);add(detail,fighter+' · market probability',comparison.market);add(detail,fighter+' · model probability',comparison.model==='50.0% · neutral 50/50 prior, NOT a prediction'?'INSUFFICIENT DATA — neutral prior only':comparison.model);add(detail,fighter+' · fair odds',comparison.fair);add(detail,fighter+' · hypothetical EV',comparison.ev)}
   add(detail,'Projection audit','Historical count-model calibration is research-only; duration and prop-line calibration unvalidated');
   add(detail,'Fight simulation','Exploratory Poisson count distribution only · NOT bout-level Monte Carlo');
   add(detail,'Market line probabilities','Exploratory count tails are not calibrated sportsbook-line hit rates');
   add(detail,'Data integrity','Fight ID, names and start checked for Elo; other inputs unverified for live use');
   add(detail,'Method / round','Not predicted — outcome and duration model unvalidated');
   add(detail,'Betting decision','RESEARCH ONLY · NO MODEL-VERIFIED EDGE');
   for(const fighter of [f.red,f.blue]){
     const stat=statsByName.get(norm(fighter));if(stat)matched++;
     const model=modelDisplay(f,fighter,stat),price=market.value==='Moneyline'?bookPrices(f,fighter):'No verified prop quote';
     if(price!=='— / —'&&price!=='No verified prop quote')priced++;
     const base=marketBaseline(f,fighter),marketPct=base.length?(base.reduce((n,x)=>n+x.novig,0)/base.length*100).toFixed(1)+'%':'No two-sided market';
     const row=document.createElement('tr');
     for(const val of [fighter,fighter===f.red?f.blue:f.red,eastern(f.start_time),market.value,model,price,marketPct,'Research only']){const td=document.createElement('td');td.textContent=val;row.append(td)}tbody.append(row);
     add(card,fighter+' · '+market.value,model.includes('NEUTRAL PRIOR')?'INSUFFICIENT DATA — neutral prior only':model);
     if(market.value==='Moneyline'){add(detail,fighter+' · DK / FD',price);add(detail,fighter+' · no-vig market',marketPct)}
   }
   cards.append(card);
 }
 count.textContent=chosen.length+' scheduled card fights (start time does not confirm completion) · '+matched+' matched fighter profiles · '+priced+' fresh priced selections · one comparison card per fight';
 if(!chosen.length)count.textContent='No scheduled UFC card fights in the current feed. This may reflect missing ESPN event coverage or a stale refresh, not an empty UFC calendar.';
}
market.addEventListener('change',render);bout.addEventListener('change',render);
const get=async path=>{const r=await fetch(path+'?reload='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(path+' unavailable');return r.json()};
Promise.all([get('./feed/ufc_research.json'),get('./feed/ufc_elo_projections.json').catch(()=>null),get('./feed/ufc_fighter_stats_mirror.json').catch(()=>null),get('./feed/mma_mixed_martial_arts.json').catch(()=>null)]).then(([data,elo,stats,book])=>{
if(data.sport!=='UFC'||!Array.isArray(data.fights))throw Error('Invalid UFC card feed');
const cardGenerated=Date.parse(data.generated_at),cardAgeHours=Number.isFinite(cardGenerated)?(Date.now()-cardGenerated)/3600000:null;
const cardFeedState=cardAgeHours===null||cardAgeHours<0?'CARD FEED TIMESTAMP UNVERIFIED':cardAgeHours>24?'STALE CARD FEED ('+cardAgeHours.toFixed(1)+'h old)':'Card feed updated '+cardAgeHours.toFixed(1)+'h ago';
if(elo&&elo.sport==='UFC'&&Array.isArray(elo.projections))for(const item of elo.projections)if(item?.fight_id)eloById.set(String(item.fight_id),item);
if(stats&&stats.sport==='UFC'&&Array.isArray(stats.fighters))for(const f of stats.fighters){if(!f.name)continue;profileByName.set(norm(f.name),f);if(f.status==='MATCHED_HISTORICAL_STATS')statsByName.set(norm(f.name),f)}
if(book&&book.sport==='mma_mixed_martial_arts'&&book.source==='the-odds-api-v4'&&book.status==='ok'&&Array.isArray(book.odds)&&Number.isFinite(Date.parse(book.fetched_at))&&Date.parse(book.fetched_at)<=Date.now()&&Date.now()-Date.parse(book.fetched_at)<=6*60*60*1000){odds=book.odds;oddsFetched=book.fetched_at}
fights=data.fights.filter(f=>f&&f.red&&f.blue&&f.id&&Number.isFinite(Date.parse(f.start_time))&&Date.parse(f.start_time)>Date.now()-36*60*60*1000).sort((a,b)=>Date.parse(a.start_time)-Date.parse(b.start_time));
for(const f of fights){const o=document.createElement('option');o.value=String(f.id);o.textContent=f.red+' vs '+f.blue+' · '+eastern(f.start_time);bout.append(o)}
p.textContent=cardFeedState+'. Scheduled fights remain visible for 36 hours after listed start; this does not verify whether a fight is live or completed. Historical strike projections are selected by default. Select another market to view available historical stats. Moneyline model is an independent uncalibrated historical striking/takedown/Elo heuristic when both fighters have data; sportsbook no-vig probability is shown separately. Strike/grappling figures are survival-adjusted research expectations using an illustrative, untrained 18% per-round finish hazard, not validated bout-specific duration or opponent-adjusted forecasts. DK / FD prices are timestamp-validated pre-fight snapshots, NOT a guarantee of currently executable odds; confirm current odds before any bet. No validated prop hit probabilities. Last odds capture: '+(oddsFetched?eastern(oddsFetched):'unavailable')+'.';
render();
}).catch(e=>{count.textContent='UNAVAILABLE — '+e.message});
})();