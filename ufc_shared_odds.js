(()=>{'use strict';
const root=document.getElementById('ksl-shared-odds');if(!root)return;
const make=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n};
root.append(make('h2','DraftKings / FanDuel · Saved Sportsbook Prices'));
root.append(make('p','Uses the same authorized sportsbook snapshot pipeline as NFL, NBA and NHL. Saved snapshots are not live; no prices are inferred or entered manually.'));
const status=make('p','Checking saved sportsbook snapshot…');status.setAttribute('role','status');root.append(status);
const wrap=make('div');wrap.style.overflowX='auto';const table=make('table');table.style.cssText='min-width:680px;width:100%;border-collapse:collapse';const tr=make('tr');for(const label of ['Matchup','Market','Selection','Line','DraftKings','FanDuel','Updated ET']){const th=make('th',label);th.style.padding='10px';tr.append(th)}table.append(tr);const body=make('tbody');table.append(body);wrap.append(table);root.append(wrap);
const fmt=p=>Number.isFinite(p)&&(p<=-100||p>=100)?(p>0?'+':'')+p:'—';
fetch('./feed/mma_mixed_martial_arts.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('No published UFC sportsbook snapshot');return r.json()}).then(d=>{
if(d.sport!=='mma_mixed_martial_arts'||d.source!=='the-odds-api-v4'||d.status!=='ok'||!Array.isArray(d.odds))throw Error('Unverified sportsbook feed');
const now=Date.now(),ts=Date.parse(d.fetched_at);
if(!Number.isFinite(ts)||now-ts>15*60*1000||ts>now+60000){status.textContent='STALE or invalid snapshot · last fetched '+(d.fetched_at||'unknown')+' · no current odds shown';return}
const grouped=new Map();
for(const q of d.odds){if(!['draftkings','fanduel'].includes(q.bookmaker)||!Number.isFinite(q.price)||!q.event_id||!q.selection||Date.parse(q.commence_time)<=now)continue;
const updated=Date.parse(q.updated_at);if(!Number.isFinite(updated)||now-updated>15*60*1000||updated>now+60000)continue;
const k=JSON.stringify([q.event_id,q.market,q.selection,q.point??null]);if(!grouped.has(k))grouped.set(k,{});grouped.get(k)[q.bookmaker]=q;
}
for(const group of grouped.values()){const a=group.draftkings,b=group.fanduel,x=a||b;if(!x)continue;const row=make('tr');for(const v of [x.event,x.market,x.selection,x.point??'—',fmt(a?.price),fmt(b?.price),new Date(x.updated_at).toLocaleString('en-US',{timeZone:'America/New_York'})]){const td=make('td',String(v));td.style.cssText='padding:10px;border-bottom:1px solid #345';row.append(td)}body.append(row)}
status.textContent=grouped.size+' fresh saved market selections · snapshot '+new Date(ts).toLocaleString('en-US',{timeZone:'America/New_York'})+' ET · availability can change · no betting recommendations implied';
}).catch(e=>{status.textContent='UNAVAILABLE — '+e.message});
})();