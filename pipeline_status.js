/* Top-of-home GitHub Actions status; read-only, no Actions jobs or paid API calls. */
(()=>{'use strict';
const repo='Donovan1019/kennys-sports-lab-mobile';
const workflows=[
  {id:'grade-nba-nhl-forecasts.yml',label:'NBA · NHL · NFL Daily',schedule:'7:20 AM / 5:15 PM EDT · 6:20 AM / 4:15 PM EST'},
  {id:'weekly-three-sport-research.yml',label:'Historical Research',schedule:'Sunday · 6:40 AM EDT / 5:40 AM EST'}
];
function mount(){
  const main=document.querySelector('main');if(!main||document.getElementById('ksl-pipeline-status'))return;
  const section=document.createElement('section');section.id='ksl-pipeline-status';
  section.setAttribute('aria-label','Pipeline status');
  section.innerHTML='<div class="ksl-status-head"><h2>⚙ Pipeline Status</h2><button type="button" id="ksl-status-refresh">↻ Check status</button></div><p class="ksl-status-sub">Latest verified GitHub Actions runs · NBA / NHL / NFL</p><div id="ksl-status-list" aria-live="polite">Loading workflow status…</div><p class="ksl-status-foot">GitHub schedules may start late. Manual runs are labeled; an older successful run does not prove today’s scheduled run completed.</p>';
  main.prepend(section);
  const list=section.querySelector('#ksl-status-list');
  const refresh=section.querySelector('#ksl-status-refresh');
  const fmt=iso=>iso?new Date(iso).toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}):'—';
  async function load(){
    refresh.disabled=true;list.textContent='Checking GitHub Actions…';
    const cards=await Promise.all(workflows.map(async w=>{
      const card=document.createElement('div');card.className='ksl-status-card';
      const heading=document.createElement('strong');heading.textContent=w.label;card.append(heading);
      const schedule=document.createElement('small');schedule.textContent=w.schedule;card.append(schedule);
      try{
        const url='https://api.github.com/repos/'+repo+'/actions/workflows/'+w.id+'/runs?per_page=15';
        const response=await fetch(url,{headers:{Accept:'application/vnd.github+json'},cache:'no-store'});
        if(!response.ok)throw Error('GitHub status unavailable ('+response.status+')');
        const data=await response.json();const runs=Array.isArray(data.workflow_runs)?data.workflow_runs:[];
        const latest=runs[0],scheduled=runs.find(r=>r.event==='schedule');
        const state=document.createElement('p');
        const status=r=>r.status!=='completed'?'IN PROGRESS':r.conclusion==='success'?'SUCCESS':r.conclusion==='failure'?'FAILED':String(r.conclusion||'UNKNOWN').toUpperCase();
        state.className='ksl-run-state '+(latest?.conclusion==='success'?'ksl-run-ok':latest?.conclusion==='failure'?'ksl-run-fail':'');
        state.textContent=latest?status(latest)+' · '+fmt(latest.updated_at||latest.created_at):'NO RUNS FOUND';
        card.append(state);
        const meta=document.createElement('p');meta.className='ksl-status-meta';
        meta.textContent=latest?'Latest: '+(latest.event==='schedule'?'scheduled':latest.event==='workflow_dispatch'?'manual':latest.event)+' · '+fmt(latest.created_at):'Waiting for first run';
        card.append(meta);
        const sched=document.createElement('p');sched.className='ksl-status-meta';
        sched.textContent='Last scheduled: '+(scheduled?status(scheduled)+' · '+fmt(scheduled.created_at):'not yet observed');
        card.append(sched);
        const link=document.createElement('a');link.href=latest?.html_url||'https://github.com/'+repo+'/actions/workflows/'+w.id;link.target='_blank';link.rel='noopener noreferrer';link.textContent='View GitHub logs ↗';card.append(link);
      }catch(err){const warning=document.createElement('p');warning.className='ksl-run-state';warning.textContent='STATUS UNAVAILABLE — '+err.message;card.append(warning);
        const link=document.createElement('a');link.href='https://github.com/'+repo+'/actions/workflows/'+w.id;link.textContent='Open workflow ↗';card.append(link)}
      return card;
    }));
    list.replaceChildren(...cards);refresh.disabled=false;
  }
  refresh.addEventListener('click',load);load();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
