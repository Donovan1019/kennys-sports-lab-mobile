/* Supplemental ESPN injury source; separate from official inactive verification. */
(()=>{'use strict';if(window.KSL_ACTIVE_SPORT!=='NFL')return;
const parent=document.getElementById('nfl-injury-report');if(!parent)return;
const wrap=document.createElement('section');wrap.id='nfl-espn-injury-live';wrap.style.cssText='border-top:1px solid #303234;padding:14px 0;color:#f5f5f5';
const h=document.createElement('h3');h.textContent='ESPN injury source · live reference';wrap.append(h);
const state=document.createElement('p');state.setAttribute('role','status');state.textContent='Checking ESPN league injury feed…';wrap.append(state);
const list=document.createElement('div');wrap.append(list);parent.append(wrap);
const source=document.createElement('a');source.href='https://www.espn.com/nfl/injuries';source.target='_blank';source.rel='noopener noreferrer';source.textContent='Cross-check ESPN injury reports';source.style.color='#f3c621';wrap.append(source);
const text=x=>String(x??'').trim();
const teams=new Set(['NE','DET','KC','ATL','BUF','NYJ','MIA','IND','MIN','GB','CAR','NO','JAX','TEN','HOU','CLE','SEA','LV','LAR','ARI','SF','DAL','PIT','CIN']);
async function load(){try{const r=await fetch('https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();
const groups=Array.isArray(d.injuries)?d.injuries:Array.isArray(d.items)?d.items:[];let count=0;
for(const group of groups){const name=text(group.team?.displayName||group.team?.name||group.displayName);const rows=Array.isArray(group.injuries)?group.injuries:[];if(!name||!rows.length)continue;
const box=document.createElement('details');const title=document.createElement('summary');title.textContent=name+' · '+rows.length+' entries';box.append(title);
for(const item of rows.slice(0,40)){const player=text(item.athlete?.displayName||item.athlete?.fullName||item.player?.displayName);const status=text(item.status||item.type?.description||item.details?.type||'Status not provided');if(!player)continue;const p=document.createElement('p');p.textContent=player+' · '+status;box.append(p);count++}list.append(box)}
if(!count)throw Error('Response schema contains no recognizable player injury entries');
state.textContent=count+' ESPN injury entries · fetched '+new Date().toLocaleTimeString('en-US',{timeZone:'America/New_York'})+' ET · reference only; not official game-day inactives or model-adjusted projections.';
}catch(e){list.replaceChildren();state.textContent='ESPN INJURY FEED UNAVAILABLE · '+e.message+'. Saved injury reports remain separate; do not infer active status.'}}
load();
})();