/* Native NBA coaches news cards from a periodically refreshed, attributed public-news RSS snapshot. */
(()=>{'use strict';
const parent=document.getElementById('ksl-nba');if(!parent)return;
const section=document.createElement('section');section.id='ksl-nba-coaches-news';section.setAttribute('aria-label','NBA Coaches News');
const css=document.createElement('style');css.textContent='#ksl-nba-coaches-news{padding:16px;margin:0 0 20px;border:1px solid #366f56;border-radius:14px;background:#0c2030;color:#e6f3fa}#ksl-nba-coaches-news h3{margin:0 0 6px;color:#80f8aa}#ksl-nba-coaches-news p{color:#afc6d4;font-size:13px;line-height:1.5}#ksl-nba-coaches-news .ksl-coach-list{display:grid;gap:10px;margin-top:12px}#ksl-nba-coaches-news article{background:#102b3d;border:1px solid #33516a;border-radius:10px;padding:12px}#ksl-nba-coaches-news article a{color:#b1f8c6;font-weight:750;text-decoration:none;overflow-wrap:anywhere}#ksl-nba-coaches-news article small{display:block;color:#a7bdd1;margin-top:8px}#ksl-nba-coaches-news .ksl-coach-source{color:#a5bed3}#ksl-nba-coaches-news .ksl-coach-source a{color:#b1f8c6}';document.head.append(css);
const heading=document.createElement('h3');heading.textContent='NBA · Coaches News Feed';
const info=document.createElement('p');info.textContent='Recent publicly indexed coaching, rotation and player-usage reporting, displayed as news cards. Sources and timestamps accompany each item.';
const state=document.createElement('p');state.setAttribute('role','status');state.textContent='Loading saved coaching news…';
const list=document.createElement('div');list.className='ksl-coach-list';
const attribution=document.createElement('p');attribution.className='ksl-coach-source';attribution.textContent='Independent reporting collected from public Google News RSS results. Full Court Press Coachspeak is a separate research source: ';
const fcp=document.createElement('a');fcp.href='https://fcp.news/coachspeak';fcp.target='_blank';fcp.rel='noopener noreferrer';fcp.textContent='Full Court Press ↗';attribution.append(fcp);
section.append(heading,info,state,list,attribution);parent.prepend(section);
fetch('feed/nba_coaches_news.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('snapshot unavailable');return r.json()}).then(data=>{
const items=Array.isArray(data.items)?data.items.filter(x=>x&&typeof x.title==='string'&&/^https:\/\//.test(x.url||'')):[];
state.textContent=items.length?items.length+' articles · last refreshed '+(data.fetched_at||'unknown'):'No verified public coaching-news articles in the current snapshot.';
for(const x of items.slice(0,20)){const article=document.createElement('article');const a=document.createElement('a');a.href=x.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=x.title;const small=document.createElement('small');small.textContent=[x.source,x.published].filter(Boolean).join(' · ');article.append(a,small);list.append(article)}
}).catch(()=>{state.textContent='News feed currently unavailable. No headlines are being fabricated.'});
})();