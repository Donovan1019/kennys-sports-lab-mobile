const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('pfl_board_recovery.js','utf8');
const data=JSON.parse(fs.readFileSync('data/pfl/events.json','utf8'));
async function check(fail=false){
 const ids=['fight-search','market','sort','only-ready','fight-board','fight-count','fight-label','ml-count','totals-count','edge-count','feed-status','coverage-label','history-state','odds-state','sim-state'];
 const els=Object.fromEntries(ids.map(id=>[id,{value:id==='only-ready'?'all':id==='sort'?'date':'',textContent:'',innerHTML:id==='fight-board'?'STATIC FALLBACK':'',addEventListener(){}}]));
 const document={getElementById:id=>els[id]};
 const fetch=async()=>{if(fail)throw Error('offline');return {ok:true,json:async()=>data}};
 vm.runInNewContext(source,{document,window:{},fetch,Date,Intl,Number,String,Array,Math,Error});
 for(let i=0;i<10;i++)await new Promise(resolve=>setImmediate(resolve));
 if(fail){assert.equal(els['fight-board'].innerHTML,'STATIC FALLBACK');return}
 const cards=(els['fight-board'].innerHTML.match(/class="ksl-pfl-fight"/g)||[]).length;
 assert.equal(cards,Number(els['fight-count'].textContent));
 assert(!els['fight-board'].innerHTML.includes('2026-10-16'),'completed October fight leaked');
 assert(cards>0,'upcoming board unexpectedly blank');
}
(async()=>{await check();await check(true);console.log('PFL recovery smoke tests passed')})().catch(e=>{console.error(e);process.exitCode=1});
