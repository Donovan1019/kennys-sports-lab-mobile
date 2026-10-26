/* Compact intra-NFL navigation placed at the marked area above NFL heading. */
(()=>{'use strict';if(window.KSL_ACTIVE_SPORT!=='NFL')return;
const shell=document.querySelector('main.ksl-shell');if(!shell)return;
const heading=shell.querySelector('h1');if(!heading)return;
const nav=document.createElement('nav');nav.id='nfl-module-navigation';nav.setAttribute('aria-label','Jump to NFL module');
nav.style.cssText='display:flex;gap:8px;overflow-x:auto;overflow-y:hidden;white-space:nowrap;width:100%;max-width:100%;box-sizing:border-box;touch-action:pan-x pan-y;overscroll-behavior-x:contain;padding:10px 2px 14px;margin:0 0 12px;scrollbar-width:thin;-webkit-overflow-scrolling:touch';
const targets=[
['Projections','#nfl-player-projections'],
['SGP Stack Finder','#nfl-sgp-stack-finder'],
['Game markets','#nfl-game-projections'],
['Player stats','#ksl-stat-root'],
['Full Results','#nfl-full-results'],
['Research','#ksl-research-root'],
['Betting tool','./betting-ready-simulator.html?sport=NFL']
];
for(const [label,target] of targets){const a=document.createElement('a');a.textContent=label;a.href=target;a.style.cssText='display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;border:1px solid #45687d;border-radius:10px;background:#10283a;color:#eaf4ff;padding:10px 13px;font-weight:650;text-decoration:none;font-size:14px;min-height:40px';if(target.startsWith('#'))a.addEventListener('click',e=>{const element=document.querySelector(target);if(!element){e.preventDefault();return}e.preventDefault();element.scrollIntoView({behavior:'smooth',block:'start'});history.replaceState(null,'',target)});nav.append(a)}
heading.parentNode.insertBefore(nav,heading);
})();
