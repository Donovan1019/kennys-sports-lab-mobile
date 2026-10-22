(()=>{'use strict';
const root=document.getElementById('matchup-location');if(!root)return;
const info=document.createElement('p');info.textContent='Experimental historical matchup simulation: 10,000 resampled score scenarios per game. No injury, lineup, pace, opponent-strength or calibration adjustments. Research only — never a verified pick.';root.insertBefore(info,document.getElementById('ksl-context-games'));
let token=0;
const seedRand=(seed)=>()=>{seed=(Math.imul(seed,1664525)+1013904223)|0;return(seed>>>0)/4294967296};
const hash=s=>[...s].reduce((v,c)=>(Math.imul(v,31)+c.charCodeAt(0))|0,157);
const finite=x=>typeof x==='number'&&Number.isFinite(x);
function simulate(game,spread,total){
const away=(game.teams||[]).find(t=>t.team===game.away),home=(game.teams||[]).find(t=>t.team===game.home);
if(!away||!home)throw Error('Team matchup data missing');
const rows=t=>(t.score_history||[]).filter(g=>finite(g.scored)&&finite(g.allowed)&&Date.parse(g.date)<Date.parse(game.commence_time));
const ah=rows(away),hh=rows(home);if(ah.length<15||hh.length<15)throw Error('Need at least 15 historical games for both teams');
const rng=seedRand(hash(game.event_id+String(spread)+String(total)));let aw=0,hw=0,ties=0,cover=0,coverPush=0,over=0,totalPush=0,as=0,hs=0;
for(let i=0;i<10000;i++){
const a=ah[Math.floor(rng()*ah.length)],h=hh[Math.floor(rng()*hh.length)];
const aScore=Math.max(0,Math.round((a.scored+h.allowed)/2));
const hScore=Math.max(0,Math.round((h.scored+a.allowed)/2));
as+=aScore;hs+=hScore;if(aScore>hScore)aw++;else if(hScore>aScore)hw++;else ties++;
const margin=hScore-aScore+spread;if(margin>0)cover++;else if(margin===0)coverPush++;
const combined=hScore+aScore;if(combined>total)over++;else if(combined===total)totalPush++;
}
return {awayMean:as/10000,homeMean:hs/10000,awayWin:aw/10000,homeWin:hw/10000,ties:ties/10000,homeCover:cover/10000,coverPush:coverPush/10000,over:over/10000,totalPush:totalPush/10000,samples:Math.min(ah.length,hh.length)};
}
function attach(){
const list=document.getElementById('ksl-context-games');if(!list)return;
for(const item of list.querySelectorAll('details')){
if(item.dataset.simReady)continue;item.dataset.simReady='1';
const summary=item.querySelector('summary');const event=summary?.textContent?.split(' · ')[0];
const games=window.__kslMatchupGames||[];const game=games.find(g=>g.event===event);if(!game)continue;
const wrapper=document.createElement('div'),label=document.createElement('p');label.textContent='Experimental score simulator · home spread and game total (editable research thresholds)';
const spread=document.createElement('input');spread.type='number';spread.step='0.5';spread.value='0';spread.setAttribute('aria-label','Home team spread');
const total=document.createElement('input');total.type='number';total.step='0.5';total.value='220';total.setAttribute('aria-label','Game total');
const button=document.createElement('button');button.type='button';button.textContent='Run 10,000 score scenarios';const result=document.createElement('p');result.setAttribute('aria-live','polite');
button.onclick=()=>{try{if(spread.value===''||total.value==='')throw Error('Enter both thresholds');const a=Number(spread.value),b=Number(total.value);if(!Number.isFinite(a)||!Number.isFinite(b)||b<=0)throw Error('Invalid thresholds');const s=simulate(game,a,b),pct=x=>(100*x).toFixed(1)+'%';result.textContent='RESEARCH ONLY · '+game.away+' '+s.awayMean.toFixed(1)+' — '+game.home+' '+s.homeMean.toFixed(1)+' projected mean scores · 10,000 scenarios · Away win '+pct(s.awayWin)+' · Home win '+pct(s.homeWin)+' · Simulated ties '+pct(s.ties)+' · Home covers '+a+' '+pct(s.homeCover)+' (push '+pct(s.coverPush)+') · Over '+b+' '+pct(s.over)+' (push '+pct(s.totalPush)+'). No verified odds, EV, calibration or recommendation.';}catch(e){result.textContent='SIMULATION UNAVAILABLE: '+e.message}};
wrapper.append(label,spread,total,button,result);item.append(wrapper);
}
}
const list=document.getElementById('ksl-context-games');const observer=new MutationObserver(attach);observer.observe(list,{childList:true});attach();
})();