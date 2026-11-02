/* NFL SGP evidence policy: display source-backed blockers; never infer eligibility. */
(()=>{'use strict';
const panel=document.getElementById('nfl-sgp-readiness-policy');if(!panel)return;
const set=(message)=>{panel.textContent=message};
const get=async path=>{const r=await fetch(path+'?readiness='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(path+' unavailable');return r.json()};
Promise.all([get('./feed/nfl_sgp_walkforward_accuracy.json'),get('./feed/player_recommendation_readiness.json'),get('./feed/nfl_player_stats.json'),get('./feed/nfl_props.json')]).then(([walk,ready,stats,live])=>{
const markets=walk?.frozen_forward_holdout?.markets||{};
const failed=Object.entries(markets).filter(([,v])=>v?.eligible_for_live_use!==true).map(([name])=>name);
const nfl=ready?.sports?.NFL||{}, quotes=ready?.source_integrity?.NFL_archived_player_props||{};
const players=Array.isArray(stats?.players)?stats.players:[];
const currentQuotes=Array.isArray(live?.odds)?live.odds:[];
const now=Date.now();
const freshQuotes=currentQuotes.filter(q=>['draftkings','fanduel'].includes(q.bookmaker)&&Number.isFinite(Date.parse(q.updated_at))&&now-Date.parse(q.updated_at)>=0&&now-Date.parse(q.updated_at)<=30*60000&&Date.parse(q.commence_time)>now);
const paired=new Map();for(const q of freshQuotes){if(!['Over','Under'].includes(q.selection)||!Number.isFinite(Number(q.point)))continue;const k=[q.event_id,q.bookmaker,q.player,q.market,Number(q.point)].join('|');if(!paired.has(k))paired.set(k,new Set());paired.get(k).add(q.selection)}
const freshPairs=[...paired.values()].filter(s=>s.has('Over')&&s.has('Under')).length;
const logs=players.flatMap(p=>Array.isArray(p?.games)?p.games:[]);
const identified=logs.filter(g=>g?.game_id||g?.event_id).length;
const checks=[
 ['Player logs with event IDs',logs.length>0&&identified===logs.length,identified+'/'+logs.length],
 ['Market calibration',Object.keys(markets).length>0&&failed.length===0,failed.length+' not approved'],
 ['Verified NFL player recommendations',nfl.fully_verified_player_recommendations>0,String(nfl.fully_verified_player_recommendations||0)],
 ['Independent roster assignments',quotes.current_roster_source_connected===true&&quotes.verified_player_team_assignments>0,String(quotes.verified_player_team_assignments||0)],
 ['Fresh DK/FD prop quotes',freshQuotes.length>0,freshQuotes.length+' current pregame selections (30-minute window)'],
 ['Fresh same-book two-way lines',freshPairs>0,String(freshPairs)+' paired lines'],
 ['Independent joint SGP calibration and EV',false,'Not established']
];
panel.replaceChildren();
const title=document.createElement('h3');title.textContent='SGP evidence & betting eligibility';panel.append(title);
const summary=document.createElement('p');summary.textContent='RESEARCH ONLY — not bet eligible. Source-backed readiness gates must all pass before picks can be promoted.';summary.style.fontWeight='700';panel.append(summary);
const list=document.createElement('ul');for(const [label,ok,detail] of checks){const li=document.createElement('li');li.textContent=(ok?'PASS':'BLOCKED')+' · '+label+' · '+detail;list.append(li)}panel.append(list);
}).catch(()=>set('RESEARCH ONLY — not bet eligible. Readiness evidence feeds are missing or invalid; no SGP pick may be promoted.'));
})();
