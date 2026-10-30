(()=>{'use strict';
const root=document.getElementById('ksl-shared-odds');if(!root)return;
const make=(tag,value)=>{const n=document.createElement(tag);if(value!==undefined)n.textContent=value;return n};
root.append(make('h2','DraftKings / FanDuel · Saved Sportsbook Prices'));
root.append(make('p','Saved authorized sportsbook quotes are not live. Prices may change; historical or stale quotes are never betting recommendations.'));
const status=make('p','Loading sportsbook snapshot…');status.setAttribute('role','status');root.append(status);
const refresh=make('button','Reload saved odds');refresh.type='button';refresh.style.cssText='padding:10px 14px;margin:6px 0 14px;border-radius:8px;cursor:pointer';root.append(refresh);
const wrap=make('div');wrap.style.overflowX='auto';const table=make('table');table.style.cssText='min-width:760px;width:100%;border-collapse:collapse';
const tr=make('tr');for(const label of ['Matchup','Market','Selection','Line','DraftKings','FanDuel','Updated ET','Quote status']){const th=make('th',label);th.style.padding='10px';tr.append(th)}table.append(tr);
const body=make('tbody');table.append(body);wrap.append(table);root.append(wrap);
const fmt=p=>Number.isFinite(p)&&(p<=-100||p>=100)?(p>0?'+':'')+p:'—';
const et=ts=>new Date(ts).toLocaleString('en-US',{timeZone:'America/New_York',timeZoneName:'short'});
const FRESH_MS=15*60*1000;
function validTime(value,now){const t=Date.parse(value);return Number.isFinite(t)&&t<=now+60000?t:null}
async function load(){
refresh.disabled=true;status.textContent='Loading saved sportsbook snapshot…';body.replaceChildren();
try{
const response=await fetch('./feed/mma_mixed_martial_arts.json?reload='+Date.now(),{cache:'no-store'});
if(!response.ok)throw Error('Published UFC sportsbook file unavailable (HTTP '+response.status+')');
const d=await response.json();
if(d.sport!=='mma_mixed_martial_arts'||d.source!=='the-odds-api-v4'||d.status!=='ok'||!Array.isArray(d.odds))throw Error('Unverified UFC sportsbook feed');
const now=Date.now(),snapshot=validTime(d.fetched_at,now);
if(snapshot===null)throw Error('Invalid or future-dated sportsbook snapshot');
const grouped=new Map();let rejected=0;
for(const q of d.odds){
if(!['draftkings','fanduel'].includes(q.bookmaker)||!Number.isFinite(q.price)||(q.price>-100&&q.price<100)||!q.event_id||!q.selection||!q.market){rejected++;continue}
const start=validTime(q.commence_time,now),updated=validTime(q.updated_at,now);
if(start===null||updated===null){rejected++;continue}
if(start<=now)continue;
const k=JSON.stringify([q.event_id,q.market,q.selection,q.point??null]);
if(!grouped.has(k))grouped.set(k,{});grouped.get(k)[q.bookmaker]=q;
}
let fresh=0,stale=0;
for(const group of grouped.values()){
const a=group.draftkings,b=group.fanduel,x=a||b;if(!x)continue;
const quotes=[a,b].filter(Boolean);
const isFresh=now-snapshot<=FRESH_MS&&quotes.every(q=>now-Date.parse(q.updated_at)<=FRESH_MS);
if(isFresh)fresh++;else stale++;
const row=make('tr');
for(const v of [x.event,x.market,x.selection,x.point??'—',fmt(a?.price),fmt(b?.price),et(x.updated_at),isFresh?'Fresh saved quote':'Stale saved quote — verify before use']){
const td=make('td',String(v));td.style.cssText='padding:10px;border-bottom:1px solid #345';row.append(td)}
body.append(row);
}
status.textContent=fresh+' fresh saved selections · '+stale+' stale saved selections · snapshot '+et(d.fetched_at)+(rejected?' · '+rejected+' invalid quotes excluded':'')+'. Saved quotes remain visible for comparison; stale quotes are not current betting lines.';
if(!grouped.size)status.textContent='No valid upcoming UFC sportsbook selections in the saved snapshot · snapshot '+et(d.fetched_at);
}catch(e){status.textContent='UNAVAILABLE — '+e.message+' · retry to check published data';}
finally{refresh.disabled=false;}
}
refresh.addEventListener('click',load);load();
})();
