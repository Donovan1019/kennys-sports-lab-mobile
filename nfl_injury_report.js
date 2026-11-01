/* NFL injury and official inactive timing. No fabricated player status. */
(()=>{'use strict';if(window.KSL_ACTIVE_SPORT!=='NFL')return;
const shell=document.querySelector('main.ksl-shell');if(!shell)return;
const section=document.createElement('section');section.id='nfl-injury-report';section.style.cssText='border:1px solid #45687d;border-radius:12px;padding:14px;margin:18px 0;background:#10283a;color:#eaf4ff;scroll-margin-top:24px';
const h=document.createElement('h2');h.textContent='NFL Injury Report & Official Inactives';section.append(h);
const intro=document.createElement('p');intro.textContent='Official inactive lists are typically published 90 minutes before each kickoff. A scheduled release is NOT confirmation. Player injury statuses remain unverified until a sourced report is successfully loaded.';section.append(intro);
const status=document.createElement('p'),list=document.createElement('div');section.append(status,list);
const button=document.createElement('button');button.type='button';button.textContent='Refresh game schedules / inactive deadlines';button.style.cssText='padding:10px;border-radius:8px;cursor:pointer';section.append(button);
const et=x=>new Date(x).toLocaleString('en-US',{timeZone:'America/New_York',weekday:'short',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'});
const clean=x=>String(x||'').trim();
async function refresh(){status.textContent='Checking published NFL game schedule…';list.replaceChildren();try{
const r=await fetch('./feed/independent_game_inputs.json?injury_schedule='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);
const d=await r.json();const games=(Array.isArray(d.games)?d.games:[]).filter(g=>Number.isFinite(Date.parse(g.commence_time))&&Date.parse(g.commence_time)>Date.now()).sort((a,b)=>Date.parse(a.commence_time)-Date.parse(b.commence_time)).slice(0,32);
status.textContent=games.length?'Schedule source: saved NFL matchup feed · Injury data: NOT CONNECTED · No player inactive status inferred':'No upcoming games in saved schedule. Injury reports unavailable.';
for(const g of games){const kickoff=Date.parse(g.commence_time),release=kickoff-90*60000;const card=document.createElement('article');card.style.cssText='border-top:1px solid #45687d;padding:12px 0';const title=document.createElement('h3');title.textContent=clean(g.event)||clean(g.away)+' @ '+clean(g.home);card.append(title);
for(const [label,value] of [['Kickoff',et(kickoff)],['Expected official inactives',et(release)],['Report window',Date.now()<release?'Pending — not yet due':'Release window reached — verification unavailable'],['Official player status','UNVERIFIED — no sourced inactive list'],['Projection impact','NOT APPLIED — player participation unknown']]){const p=document.createElement('p');p.textContent=label+': '+value;card.append(p)}list.append(card)}
}catch(e){status.textContent='Schedule unavailable: '+e.message+'. Official injury and inactive reports remain UNVERIFIED.'}}
button.addEventListener('click',refresh);
const anchor=document.getElementById('nfl-full-results')||document.getElementById('ksl-research-root');if(anchor)anchor.parentNode.insertBefore(section,anchor);else shell.append(section);
refresh();
})();