/* PFL per-fight Kenny projection simulator. Exploratory only; no invented inputs. */
(function(){'use strict';
const $=id=>document.getElementById(id);
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const hash=s=>{let h=2166136261;for(const c of String(s))h=Math.imul(h^c.charCodeAt(0),16777619);return h>>>0};
const rand=seed=>{let x=seed>>>0;return()=>((x=(Math.imul(x,1664525)+1013904223)>>>0)/4294967296)};
let projections=new Map(),loaded=false;
const simulationCache=new Map();
function attach(){
 const board=$('fight-board');if(!board)return;
 for(const card of board.querySelectorAll('article.ksl-pfl-fight')){
  const id=card.getAttribute('data-fight-id')||card.dataset.fightId;
  if(!id)continue;
  const existing=card.querySelector('.ksl-pfl-sim-result');
  if(existing){run(id,existing);continue;}
  const wrap=document.createElement('div');wrap.className='ksl-pfl-simulator';
  const result=document.createElement('div');result.className='ksl-pfl-sim-result';result.setAttribute('aria-live','polite');
  wrap.append(result);card.append(wrap);
  run(id,result);
 }
}
function run(id,output){
 const p=projections.get(id);
 if(!loaded){output.textContent='Loading Kenny’s published projection inputs…';return}
 if(!p||p.available!==true||!Number.isFinite(p.probabilityA)||!Array.isArray(p.fighters)||p.fighters.length!==2){output.textContent='SIMULATION UNAVAILABLE · Insufficient verified fighter history. No fabricated winner or rounds projection.';return}
 let prob=simulationCache.get(id);
 if(prob===undefined){const random=rand(hash(id));let wins=0;for(let i=0;i<50000;i++)if(random()<p.probabilityA)wins++;prob=wins/50000;simulationCache.set(id,prob)}
 const first=prob>=.5,winner=p.fighters[first?0:1].replace(/-/g,' ');
 output.innerHTML='<strong class="ksl-pfl-sim-pick">Kenny’s exploratory winner: '+escape(winner)+'</strong><div>50,000 reproducible Monte Carlo draws · '+(100*Math.max(prob,1-prob)).toFixed(2)+'% winner probability</div><small>Source: published PFL historical feature model · Independent calibration: unavailable · Total-round simulator: unavailable (finish-time inputs missing) · Betting-ready: NO</small>';
}
function load(){
 if(!window.KSLPFLFeed?.load){loaded=true;attach();return}
 window.KSLPFLFeed.load().then(feed=>{projections=new Map((feed.projections?.bouts||[]).map(x=>[String(x.boutId),x]));loaded=true;attach()}).catch(()=>{loaded=true;attach()});
}
const board=$('fight-board');if(!board)return;
const observer=new MutationObserver(()=>{observer.disconnect();attach();observer.observe(board,{childList:true})});
observer.observe(board,{childList:true});
attach();load();
})();