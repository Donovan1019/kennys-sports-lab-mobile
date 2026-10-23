/* UFC free odds entry: local, research-only, no external sportsbook requests. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const books={draftkings:"DraftKings",fanduel:"FanDuel"};
const storageKey="ksl-ufc-free-odds-v1";
function americanDecimal(x){return x>0?1+x/100:1+100/Math.abs(x)}
function validOdds(x){return Number.isInteger(x)&&(x<=-100||x>=100)}
function now(){return new Date().toISOString()}
function load(){try{const rows=JSON.parse(localStorage.getItem(storageKey)||"[]");return Array.isArray(rows)?rows:[]}catch{return []}}
function save(rows){localStorage.setItem(storageKey,JSON.stringify(rows))}
function message(s){$("ufc-free-status").textContent=s}
function render(){
const rows=load(),tbody=$("ufc-free-rows");tbody.replaceChildren();
for(const [i,x] of rows.entries()){
const tr=document.createElement("tr");
for(const v of [books[x.book]||x.book,x.fighter+" vs "+x.opponent,
x.fighterOdds>0?"+"+x.fighterOdds:x.fighterOdds,
x.opponentOdds>0?"+"+x.opponentOdds:x.opponentOdds,
new Date(x.capturedAt).toLocaleString(),x.eventStart]){
const td=document.createElement("td");td.textContent=String(v);tr.append(td)}
const td=document.createElement("td");const remove=document.createElement("button");
remove.type="button";remove.textContent="Remove";remove.onclick=()=>{const next=load();next.splice(i,1);save(next);render()};td.append(remove);tr.append(td);tbody.append(tr)}
$("ufc-free-count").textContent=rows.length+" saved quote"+(rows.length===1?"":"s")+" on this device · not verified";
const grouped=new Map();
for(const x of rows){const key=[x.eventId,x.fighter.toLowerCase(),x.opponent.toLowerCase()].join("|");
if(!grouped.has(key))grouped.set(key,{});grouped.get(key)[x.book]=x}
const compare=$("ufc-free-comparison");compare.replaceChildren();
for(const pair of grouped.values()){
const a=pair.draftkings,d=pair.fanduel;const p=document.createElement("p");
if(!a||!d){const x=a||d;p.textContent=x.fighter+" vs "+x.opponent+": other sportsbook unavailable"}
else{
const skew=Math.abs(Date.parse(a.capturedAt)-Date.parse(d.capturedAt))/60000;
const fresh=Math.max((Date.now()-Date.parse(a.capturedAt))/60000,(Date.now()-Date.parse(d.capturedAt))/60000);
if(a.eventStart!==d.eventStart)p.textContent=a.fighter+" vs "+a.opponent+": event times disagree";
else if(skew>5)p.textContent=a.fighter+" vs "+a.opponent+": captures more than 5 minutes apart";
else if(fresh>15||fresh<0)p.textContent=a.fighter+" vs "+a.opponent+": stale or future quote";
else{const ad=americanDecimal(a.fighterOdds),fd=americanDecimal(d.fighterOdds);
const av=1/ad,bv=1/fd;p.textContent=a.fighter+": "+(ad>fd?"DraftKings":fd>ad?"FanDuel":"Same price")+" offers better raw payout · break-even DK "+(av*100).toFixed(1)+"%, FD "+(bv*100).toFixed(1)+"% · EV unavailable without independently calibrated model probability"}
}
compare.append(p)}
if(!grouped.size)compare.textContent="No saved quotes. Enter both books for the same fight to compare.";
}
function add(e){e.preventDefault();
const book=$("ufc-free-book").value,fighter=$("ufc-free-fighter").value.trim(),
opponent=$("ufc-free-opponent").value.trim(),eventId=$("ufc-free-event").value.trim(),
fighterOdds=Number($("ufc-free-fighter-odds").value),opponentOdds=Number($("ufc-free-opponent-odds").value),
eventStart=$("ufc-free-start").value;
if(!eventId||!fighter||!opponent||fighter.toLowerCase()===opponent.toLowerCase()||!validOdds(fighterOdds)||!validOdds(opponentOdds)||!eventStart){message("Invalid entry: enter two different fighters, both American odds (at least +100 or at most -100), event ID and start.");return}
const eventTime=new Date(eventStart).getTime();if(!Number.isFinite(eventTime)||eventTime<=Date.now()){message("Event must be in the future.");return}
const row={book,eventId,fighter,opponent,fighterOdds,opponentOdds,eventStart:new Date(eventTime).toISOString(),capturedAt:now()};
const rows=load().filter(x=>!(x.book===book&&x.eventId===eventId&&x.fighter.toLowerCase()===fighter.toLowerCase()&&x.opponent.toLowerCase()===opponent.toLowerCase()));
rows.push(row);save(rows);message("Saved locally. Price is user-entered and unverified; not a betting recommendation.");render()}
function exportJson(){
const rows=load(),capturedAt=now();
const data={captured_at_utc:capturedAt,entries:rows.map(x=>({book:x.book,event_id:x.eventId,fighter:x.fighter,opponent:x.opponent,fighter_odds:x.fighterOdds,opponent_odds:x.opponentOdds,event_start_utc:x.eventStart,observed_at_utc:x.capturedAt}))};
const blob=new Blob([JSON.stringify(data,null,2)],{type:"application/json"});
const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="ufc-free-odds.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function init(){if(!$("ufc-free-form"))return;$("ufc-free-form").addEventListener("submit",add);$("ufc-free-export").addEventListener("click",exportJson);$("ufc-free-clear").addEventListener("click",()=>{if(confirm("Clear all locally saved UFC odds?")){save([]);render();message("Local quotes cleared.")}});render()}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();
