(()=>{'use strict';
const root=document.getElementById('ksl-ufc-projection');if(!root)return;
const markets=['Moneyline','KO/TKO win','Submission win','Decision win','Disqualification win','Fight goes distance','Fight ends inside distance','Total rounds','Alternate rounds','Round 1 winner','Round 2 winner','Round 3 winner','Round 4 winner','Round 5 winner','Exact finish round','Method and round','Double chance','Significant strikes landed','Significant strikes attempted','Total strikes landed','Takedowns landed','Takedowns attempted','Submission attempts','Knockdowns','Control time','Combined significant strikes','Combined takedowns','Round-specific strikes','Round-specific takedowns','Fight duration','Starts round 2/3/4/5','Reaches end of round','First 60/90/120 seconds finish','Live moneyline','Live round totals','Event parlay / SGP','Alternate fighter props'];
const h=document.createElement('h2');h.textContent='📈 Fighter Projections · Model Estimates';root.append(h);
const p=document.createElement('p');p.textContent='Scheduled UFC matchup research. Every supported market can be selected. Numerical projections, probability, sportsbook lines and EV are unavailable without validated fighter inputs and verified odds. Historical records alone do not establish fight readiness.';root.append(p);
const controls=document.createElement('div');controls.className='ksl-ufc-controls';root.append(controls);
const market=document.createElement('select'),bout=document.createElement('select');market.setAttribute('aria-label','UFC projection market');bout.setAttribute('aria-label','UFC matchup');for(const m of markets){const o=document.createElement('option');o.value=m;o.textContent=m;market.append(o)}const all=document.createElement('option');all.value='';all.textContent='All upcoming matchups';bout.append(all);controls.append(market,bout);
const count=document.createElement('p');count.setAttribute('role','status');root.append(count);
const wrap=document.createElement('div');wrap.className='ksl-ufc-table-wrap';const table=document.createElement('table');const thead=document.createElement('thead');const tr=document.createElement('tr');for(const name of ['Fighter','Opponent','Start ET','Market','Model / baseline','DK / FD','Market %','Status']){const th=document.createElement('th');th.textContent=name;tr.append(th)}thead.append(tr);table.append(thead);const tbody=document.createElement('tbody');table.append(tbody);wrap.append(table);root.append(wrap);const cards=document.createElement('div');cards.className='ksl-ufc-projection-cards';root.append(cards);
let fights=[],eloById=new Map(),statsByName=new Map(),odds=[],oddsFetched=null;
const norm=s=>String(s||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9 ]/g,'').replace(/\s+/g,' ').trim();
function eastern(s){const d=new Date(s);return Number.isFinite(d.getTime())?d.toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}):'UNVERIFIED'}
const fmt=p=>Number.isFinite(p)&&(p<=-100||p>=100)?(p>0?'+':'')+p:'—';
const validQuote=q=>q&&['draftkings','fanduel'].includes(q.bookmaker)&&Number.isFinite(q.price)&&(q.price<=-100||q.price>=100)&&Date.parse(q.commence_time)>Date.now()&&Number.isFinite(Date.parse(q.updated_at))&&Date.parse(q.updated_at)<=Date.now()+60000;
function implied(a){return a<0?(-a)/((-a)+100):100/(a+100)}
function quoteGroup(f,book){const target=[norm(f.red),norm(f.blue)];return odds.filter(q=>q.market==='h2h'&&q.bookmaker===book&&validQuote(q)&&target.includes(norm(q.selection))&&target.every(n=>norm(q.event).includes(n)));}
function marketBaseline(f,fighter){const results=[];for(const book of ['draftkings','fanduel']){const rows=quoteGroup(f,book),a=rows.find(q=>norm(q.selection)===norm(fighter)),other=rows.find(q=>norm(q.selection)===norm(fighter===f.red?f.blue:f.red));if(a&&other){const p=implied(a.price),q=implied(other.price);results.push({book,price:a.price,novig:p/(p+q),timestamp:a.updated_at})}}return results}
function bookPrices(f,fighter){const results=marketBaseline(f,fighter);return ['draftkings','fanduel'].map(book=>{const x=results.find(v=>v.book===book);return x?fmt(x.price):'—'}).join(' / ')}
// Transparent first-pass research heuristic. NOT a trained/calibrated probability model.
function careerRate(s,k){const t=s?.career_round_totals;return t&&t.round_rows>0&&Number.isFinite(t[k])?t[k]/t.round_rows:null}
function independentWinEstimate(f,fighter){
  const self=statsByName.get(norm(fighter)),opp=statsByName.get(norm(fighter===f.red?f.blue:f.red));
  if(!self||!opp)return null;
  const sr=careerRate(self,'sig_landed'),or=careerRate(opp,'sig_landed'),st=careerRate(self,'td_landed'),ot=careerRate(opp,'td_landed');
  if([sr,or,st,ot].some(v=>v===null))return null;
  const es=eloById.get(String(f.id));
  const selfElo=es?(fighter===f.red?es.red_elo:es.blue_elo):null;
  const oppElo=es?(fighter===f.red?es.blue_elo:es.red_elo):null;
  const eloTerm=Number.isFinite(selfElo)&&Number.isFinite(oppElo)?Math.max(-0.65,Math.min(0.65,(selfElo-oppElo)/500)):0;
  // Regularized, bounded, symmetric score: strike rate + takedown rate + available Elo.
  const strikeTerm=Math.max(-0.5,Math.min(0.5,Math.log((sr+3)/(or+3))*0.45));
  const takedownTerm=Math.max(-0.3,Math.min(0.3,Math.log((st+0.5)/(ot+0.5))*0.18));
  const score=eloTerm+strikeTerm+takedownTerm;
  const probability=1/(1+Math.exp(-score));
  return {probability,source:'UNCALIBRATED HEURISTIC',rounds:Math.min(self.career_round_totals.round_rows,opp.career_round_totals.round_rows)};
}
function researchProjection(f,fighter,stat){
  const opponent=statsByName.get(norm(fighter===f.red?f.blue:f.red));
  const m={'Significant strikes landed':'sig_landed','Significant strikes attempted':'sig_attempted','Total strikes landed':'total_landed','Takedowns landed':'td_landed','Takedowns attempted':'td_attempted','Submission attempts':'submission_attempts','Knockdowns':'knockdowns','Control time':'control_seconds'}[market.value];
  if(!m)return null;
  const own=careerRate(stat,m);if(own===null)return null;
  // 3-round equivalent rather than assuming the bout is scheduled for three rounds.
  // Opponent exposure is not available in the current mirror, so shrink to neutral league-style
  // conservative adjustment of 1.0, not a fabricated opponent defensive figure.
  return {value:own*3,units:m==='control_seconds'?'sec / 3-round equivalent':'per 3-round equivalent',rounds:stat.career_round_totals.round_rows};
}
function modelDisplay(f,fighter,stat){
if(market.value==='Moneyline'){
  const independent=independentWinEstimate(f,fighter);
  return independent?(independent.probability*100).toFixed(1)+'% research estimate':'NO INDEPENDENT ESTIMATE';
}
const projected=researchProjection(f,fighter,stat);
return projected?projected.value.toFixed(1)+' '+projected.units:'NO MATCHED STAT SAMPLE';
}
function render(){tbody.replaceChildren();cards.replaceChildren();const chosen=fights.filter(f=>!bout.value||String(f.id)===bout.value);let withStats=0,withOdds=0;for(const f of chosen){for(const [fighter,opponent] of [[f.red,f.blue],[f.blue,f.red]]){const row=document.createElement('tr');const stat=statsByName.get(norm(fighter));const model=modelDisplay(f,fighter,stat);const price=market.value==='Moneyline'?bookPrices(f,fighter):'NO VERIFIED QUOTE';if(stat)withStats++;if(price!=='— / —'&&price!=='NO VERIFIED QUOTE')withOdds++;const independent=market.value==='Moneyline'?independentWinEstimate(f,fighter):null;const projection=market.value!=='Moneyline'?researchProjection(f,fighter,stat):null;const label=market.value==='Moneyline'?(independent?'Independent historical rate + Elo heuristic; UNCALIBRATED; min matched rounds '+independent.rounds:'No matched two-fighter stats for independent estimate'):(projection?'Historical 3-round equivalent from '+projection.rounds+' recorded rounds; NOT opponent-adjusted':'Insufficient fighter history or market not modeled');const baseline=market.value==='Moneyline'?marketBaseline(f,fighter):[];const marketPct=baseline.length?(baseline.reduce((a,x)=>a+x.novig,0)/baseline.length*100).toFixed(1)+'% no-vig market':'NO MARKET PROBABILITY';const values=[fighter,opponent,eastern(f.start_time),market.value,model,price,marketPct,label];const labels=['Fighter','Opponent','Start ET','Market','Model / history','DK / FD','Market probability','Status'];for(let i=0;i<values.length;i++){const td=document.createElement('td');td.textContent=values[i];td.setAttribute('data-label',labels[i]);row.append(td)}tbody.append(row);const card=document.createElement('article');card.className='ksl-ufc-projection-card';const title=document.createElement('h3');title.textContent=fighter;card.append(title);for(let i=1;i<values.length;i++){const line=document.createElement('div');line.className='ksl-ufc-projection-field';const k=document.createElement('span');k.textContent=labels[i];const v=document.createElement('strong');v.textContent=values[i];line.append(k,v);card.append(line)}cards.append(card)}}count.textContent=chosen.length+' upcoming matchups · '+withStats+' matched historical fighter profiles · '+withOdds+' price rows · no validated prop hit probabilities';if(!chosen.length)count.textContent='No upcoming UFC matchups available.'}
market.addEventListener('change',render);bout.addEventListener('change',render);
const get=async path=>{const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error(path+' unavailable');return r.json()};
Promise.all([get('./feed/ufc_research.json'),get('./feed/ufc_elo_projections.json').catch(()=>null),get('./feed/ufc_fighter_stats_mirror.json').catch(()=>null),get('./feed/mma_mixed_martial_arts.json').catch(()=>null)]).then(([data,elo,stats,book])=>{
if(data.sport!=='UFC'||!Array.isArray(data.fights))throw Error('Invalid UFC card feed');
if(elo&&elo.sport==='UFC'&&elo.bet_eligible===false&&elo.historical_source_independently_verified===false&&Array.isArray(elo.projections))for(const item of elo.projections)if(item?.fight_id)eloById.set(String(item.fight_id),item);
if(stats&&stats.sport==='UFC'&&stats.bet_eligible===false&&stats.research_only===true&&Array.isArray(stats.fighters))for(const f of stats.fighters)if(f.status==='MATCHED_HISTORICAL_STATS'&&f.name)statsByName.set(norm(f.name),f);
if(book&&book.sport==='mma_mixed_martial_arts'&&book.source==='the-odds-api-v4'&&book.status==='ok'&&Array.isArray(book.odds)&&Number.isFinite(Date.parse(book.fetched_at))&&Date.parse(book.fetched_at)<=Date.now()+60000){odds=book.odds;oddsFetched=book.fetched_at}
fights=data.fights.filter(f=>f&&f.red&&f.blue&&f.id&&Number.isFinite(Date.parse(f.start_time))&&Date.parse(f.start_time)>Date.now()).sort((a,b)=>Date.parse(a.start_time)-Date.parse(b.start_time));
for(const f of fights){const o=document.createElement('option');o.value=String(f.id);o.textContent=f.red+' vs '+f.blue+' · '+eastern(f.start_time);bout.append(o)}
p.textContent='Select a fighter market to view available historical stats. Moneyline model is an independent uncalibrated historical striking/takedown/Elo heuristic when both fighters have data; sportsbook no-vig probability is shown separately. Strike/grappling numbers are 3-round historical equivalents, not opponent-adjusted forecasts. DK / FD prices are last recorded sportsbook snapshots, NOT live quotes; confirm current odds before any bet. No validated prop hit probabilities. Last odds capture: '+(oddsFetched?eastern(oddsFetched):'unavailable')+'.';
render();
}).catch(e=>{count.textContent='UNAVAILABLE — '+e.message});
})();