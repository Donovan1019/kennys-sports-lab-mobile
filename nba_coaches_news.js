/* NBA Coaches News: first-party section displaying Full Court Press original feed.
   Third-party framing is subject to fcp.news embed permissions. */
(()=>{'use strict';
const parent=document.getElementById('ksl-nba');if(!parent)return;
const section=document.createElement('section');section.id='ksl-nba-coaches-news';
section.setAttribute('aria-label','NBA Coaches News');
const style=document.createElement('style');
style.textContent='#ksl-nba-coaches-news{margin:0 0 20px;padding:15px;border:1px solid #376b53;border-radius:12px;background:#10241b;color:#e3f5e9}#ksl-nba-coaches-news h3{color:#79f59a;margin:0 0 8px}#ksl-nba-coaches-news p{color:#b7cebf;font-size:13px;line-height:1.5}#ksl-nba-coaches-news .ksl-fcp-controls{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}#ksl-nba-coaches-news button,#ksl-nba-coaches-news a{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:9px 12px;border:1px solid #46885e;border-radius:9px;background:#193a29;color:#b7ffc6;font-weight:700;text-decoration:none;font-size:13px}#ksl-nba-coaches-news button[aria-pressed=true]{background:#267d4c;color:#fff}#ksl-fcp-frame{width:100%;height:min(72vh,740px);min-height:440px;border:1px solid #355c4a;border-radius:9px;background:#fff}#ksl-nba-coaches-news .ksl-fcp-note{font-size:12px;color:#a9bcb0}';
document.head.append(style);
const title=document.createElement('h3');title.textContent='NBA · Coaches News Feed';
const intro=document.createElement('p');intro.textContent='Read coaching comments, rotation news, minutes and usage updates directly below. Source: Full Court Press.';
const controls=document.createElement('div');controls.className='ksl-fcp-controls';
const tabs=[['Coachspeak','https://fcp.news/coachspeak'],['Latest','https://fcp.news/'],['Injury','https://fcp.news/injury'],['Pressers','https://fcp.news/pressers']];
const frame=document.createElement('iframe');frame.id='ksl-fcp-frame';frame.title='Full Court Press NBA coaching news feed';frame.loading='lazy';frame.referrerPolicy='strict-origin-when-cross-origin';frame.src=tabs[0][1];
const buttons=[];
for(const [label,url] of tabs){const button=document.createElement('button');button.type='button';button.textContent=label;button.setAttribute('aria-pressed',String(url===frame.src));button.addEventListener('click',()=>{frame.src=url;for(const b of buttons)b.setAttribute('aria-pressed',String(b===button));});buttons.push(button);controls.append(button)}
const source=document.createElement('a');source.href='https://fcp.news/coachspeak';source.target='_blank';source.rel='noopener noreferrer';source.textContent='Open source ↗';controls.append(source);
const note=document.createElement('p');note.className='ksl-fcp-note';note.textContent='This displays the original third-party feed, not copied news. If the feed appears blank or blocked, Full Court Press may prohibit embedding; use Open source until a permitted feed/API is available. Quotes are not official injury designations. No automatic model adjustments.';
section.append(title,intro,controls,frame,note);parent.prepend(section);
})();
