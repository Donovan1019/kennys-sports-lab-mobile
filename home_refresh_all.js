/* Homepage one-click refresh: inspect every sport feed, bypass browser cache, and report source freshness.
   GitHub Pages cannot dispatch authenticated GitHub Actions; never claim upstream ingestion ran. */
(()=>{'use strict';
const root=document.getElementById('ksl-refresh-all');if(!root)return;
const feeds=[
 ['NFL','feed/americanfootball_nfl.json'],['NBA','feed/basketball_nba.json'],
 ['NHL','feed/icehockey_nhl.json'],['NCAAB','feed/basketball_ncaab.json'],
 ['WNBA','feed/basketball_wnba.json'],['UFC','feed/ufc.json'],
 ['PFL','feed/pfl.json'],['PrizePicks','feed/prizepicks.json']
];
const heading=document.createElement('h2');heading.textContent='Refresh All Sports';
const note=document.createElement('p');note.textContent='Checks newly published feed files across sports. This does not start server-side data collection.';
const button=document.createElement('button');button.type='button';button.textContent='↻ Refresh All Sports';button.style.cssText='background:#f3c621;color:#090909;border:1px solid #f3c621;font-weight:800;padding:12px 16px;border-radius:10px;min-height:44px';
const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Ready to check source freshness.';
const results=document.createElement('div');results.style.cssText='display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:8px';
root.append(heading,note,button,status,results);
function timestamp(data){for(const key of ['fetched_at','generated_at','updated_at','checked_at','as_of','timestamp']){const value=data?.[key];if(typeof value==='string'&&Number.isFinite(Date.parse(value)))return Date.parse(value)}return null}
async function check(name,path){const card=document.createElement('div');card.style.cssText='background:#18191b;border:1px solid #303234;border-radius:9px;padding:10px';const title=document.createElement('strong');title.textContent=name;const detail=document.createElement('p');detail.style.cssText='margin:6px 0 0;font-size:12px';card.append(title,detail);results.append(card);
try{const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),10000);let response;try{response=await fetch('./'+path+'?refresh='+Date.now(),{cache:'no-store',signal:controller.signal})}finally{clearTimeout(timeout)}if(!response.ok)throw Error('HTTP '+response.status);const data=await response.json();const time=timestamp(data);if(!time){detail.textContent='Published file found · timestamp unverified';detail.style.color='#e6b34a';return 'unknown'}const hours=(Date.now()-time)/3600000;detail.textContent=hours<0?'Future timestamp — check source':hours<=6?'Fresh · '+Math.round(hours*60)+' min old':'Stale · '+Math.round(hours)+' h old';detail.style.color=hours>=0&&hours<=6?'#52d49a':'#e6b34a';return hours>=0&&hours<=6?'fresh':'stale'}catch(e){detail.textContent='Unavailable · '+e.message;detail.style.color='#f08080';return 'missing'}}
let busy=false;button.addEventListener('click',async()=>{if(busy)return;busy=true;button.disabled=true;results.replaceChildren();status.textContent='Checking published feeds across all sports…';const counts={fresh:0,stale:0,unknown:0,missing:0};try{const states=await Promise.all(feeds.map(([name,path])=>check(name,path)));for(const s of states)counts[s]++;status.textContent='Check complete · '+counts.fresh+' fresh · '+counts.stale+' stale · '+counts.unknown+' unverified timestamp · '+counts.missing+' unavailable. Refresh the homepage below to reload the latest published boards.';const existing=document.getElementById('ksl-refresh-home-boards');if(existing)existing.remove();const reload=document.createElement('button');reload.id='ksl-refresh-home-boards';reload.type='button';reload.textContent='Reload homepage boards';reload.style.cssText='margin-top:8px';reload.addEventListener('click',()=>location.replace('./index.html?updated='+Date.now()));root.append(reload)}finally{busy=false;button.disabled=false}});
})();