/* NBA Coaches News: attribution-first Full Court Press research portal.
   Links to source; no scraping, republishing, or unverified injury statuses. */
(()=>{'use strict';
const parent=document.getElementById('ksl-nba');if(!parent)return;
const section=document.createElement('section');section.id='ksl-nba-coaches-news';
section.setAttribute('aria-label','NBA Coaches News');
const css=document.createElement('style');
css.textContent='#ksl-nba-coaches-news{margin-top:20px;padding:16px;border:1px solid #3d7454;border-radius:12px;background:#10241b}#ksl-nba-coaches-news h3{color:#79f59a;margin:0 0 8px}#ksl-nba-coaches-news p{color:#b7cebf;font-size:14px;line-height:1.55}#ksl-nba-coaches-news .ksl-fcp-links{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}#ksl-nba-coaches-news a{display:inline-flex;align-items:center;min-height:44px;border:1px solid #46885e;background:#193a29;border-radius:9px;padding:10px 12px;color:#b7ffc6;font-weight:700;text-decoration:none}#ksl-nba-coaches-news a:focus-visible{outline:3px solid #81ff9a}#ksl-nba-coaches-news .ksl-fcp-note{font-size:12px;color:#a9bcb0}';
document.head.append(css);
const heading=document.createElement('h3');heading.textContent='NBA · Coaches News | Full Court Press';
const intro=document.createElement('p');intro.textContent='Coach and player interviews, beat-reporter updates, rotation plans, minutes and usage, injury recovery, and gameplan comments. Open the original source to verify context and timestamps.';
const links=document.createElement('div');links.className='ksl-fcp-links';
for(const [name,url] of [['Open Full Court Press','https://fcp.news/']]){
 const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=name+' ↗';links.append(a);
}
const note=document.createElement('p');note.className='ksl-fcp-note';note.textContent='Research source: Full Court Press (fcp.news), an independent third-party website. Quotes are not official lineup or injury designations. Some content requires a free account. This panel does not scrape content or automatically adjust model probabilities.';
section.append(heading,intro,links,note);parent.append(section);
})();
