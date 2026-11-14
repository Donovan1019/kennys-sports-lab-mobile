/* PFL per-fight Kenny projection simulator. Exploratory only; no invented inputs. */
(function(){'use strict';
const $=id=>document.getElementById(id);
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let projections=new Map(),loaded=false;
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
 if(p.monteCarlo?.simulationVerified!==true||!Number.isInteger(p.monteCarlo.iterations)||p.monteCarlo.iterations<50000||!Number.isFinite(p.probabilityB)||Math.abs(p.probabilityA+p.probabilityB-1)>.02){output.textContent='SIMULATION UNAVAILABLE · Published Monte Carlo result failed integrity checks.';return}
 const prob=p.probabilityA;
 const first=prob>=.5,winner=p.fighters[first?0:1].replace(/-/g,' ');
 output.innerHTML='<strong class="ksl-pfl-sim-pick">Kenny’s exploratory winner: '+escape(winner)+'</strong><div>'+p.monteCarlo.iterations.toLocaleString()+' published Monte Carlo draws · '+(100*Math.max(prob,1-prob)).toFixed(2)+'% winner probability</div><small>Source: published PFL historical feature model · Independent calibration: unavailable · Total-round simulator: unavailable (finish-time inputs missing) · Betting-ready: NO</small>';
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