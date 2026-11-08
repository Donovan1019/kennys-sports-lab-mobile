/* Dedicated NFL Moneyline tab reuses the existing historical-scoring simulation engine. */
(()=>{'use strict';
const host=document.getElementById('nfl-moneyline-content');
const status=document.getElementById('nfl-moneyline-status');
if(!host||!status)return;
const activate=()=>{
 const engine=document.getElementById('nfl-game-projections');
 if(!engine)return false;
 if(engine.parentElement!==host)host.append(engine);
 const market=engine.querySelector('select[aria-label="Game projection market"]');
 const period=engine.querySelector('select[aria-label="Game projection period"]');
 if(market&&market.value!=='Moneyline'){market.value='Moneyline';market.dispatchEvent(new Event('change',{bubbles:true}));}
 if(period&&period.value!=='Full game'){period.value='Full game';period.dispatchEvent(new Event('change',{bubbles:true}));}
 status.textContent='Moneyline model loaded · historical team scoring, simulated win probability and verified market comparisons when available. Research only.';
 return true;
};
if(activate())return;
const observer=new MutationObserver(()=>{if(activate())observer.disconnect()});
observer.observe(document.body,{childList:true,subtree:true});
setTimeout(()=>{observer.disconnect();if(!host.querySelector('#nfl-game-projections'))status.textContent='Moneyline engine unavailable. Check NFL game-projection data and refresh.'},20000);
})();