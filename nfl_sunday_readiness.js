/* Sunday slate integrity panel: display only sourced schedule and explicit feed status. */
(function(){
'use strict';
const root=document.getElementById('nfl-sunday-readiness');if(!root)return;
const today='2026-11-15', tz='America/New_York';
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=t=>{const d=new Date(t);return Number.isNaN(+d)?'Time unavailable':new Intl.DateTimeFormat('en-US',{timeZone:tz,hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(d)};
const status=document.getElementById('nfl-sunday-status');
const list=document.getElementById('nfl-sunday-games');
async function load(){
 status.textContent='Checking current Sunday schedule and kickoff status…';
 try{
 const r=await fetch('https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261115',{cache:'no-store'});
 if(!r.ok)throw Error('schedule HTTP '+r.status);
 const data=await r.json();const events=(data.events||[]).filter(e=>new Intl.DateTimeFormat('en-CA',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(e.date))===today).sort((a,b)=>new Date(a.date)-new Date(b.date));
 if(!events.length)throw Error('No matching events returned');
 list.innerHTML=events.map(e=>{const c=e.competitions?.[0],teams=c?.competitors||[],away=teams.find(x=>x.homeAway==='away'),home=teams.find(x=>x.homeAway==='home'),state=e.status?.type?.state||'pre',name=e.status?.type?.shortDetail||'Scheduled';return '<div class="nfl-sunday-game"><strong>'+escape(away?.team?.abbreviation||'?')+' @ '+escape(home?.team?.abbreviation||'?')+'</strong><span>'+escape(fmt(e.date))+' · '+escape(name)+'</span><small>'+ (state==='pre'?'Pregame · confirm inactives and lines before modeling':state==='in'?'LIVE · exclude from pregame selections':'Final · exclude from new bets')+'</small></div>'}).join('');
 status.textContent=events.length+' scheduled games sourced from ESPN · fetched '+new Intl.DateTimeFormat('en-US',{timeZone:tz,hour:'numeric',minute:'2-digit'}).format(new Date())+' ET · odds, inactives, and model EV NOT verified by this panel.';
 }catch(err){list.textContent='Schedule unavailable; no fabricated fixtures or betting recommendations shown.';status.textContent='UNAVAILABLE · '+err.message}
}
load();
})();
