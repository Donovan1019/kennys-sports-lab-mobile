const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('nfl_combined_odds_simulations.js','utf8');
function element(){return {value:'NFL',hidden:false,disabled:false,textContent:'',children:[],append(x){this.children.push(x)},replaceChildren(){this.children=[]},addEventListener(){},setAttribute(){}}}
const elements={};for(const id of ['matchup-location','sport','ksl-context-games','nfl-combined-game','nfl-combined-body','nfl-combined-status','nfl-combined-refresh'])elements[id]=element();
elements['matchup-location'].insertBefore=()=>{};
const document={getElementById:id=>elements[id],createElement:()=>element(),addEventListener(){}};
const context={document,window:{__kslMatchupGames:[]},Date,Math,Number,String,Array,Intl,console,fetch:async()=>({ok:true,json:async()=>({odds:[]})})};
vm.runInNewContext(code,context);assert.equal(elements['nfl-combined-refresh'].disabled,false);assert.equal(elements['nfl-combined-view'],undefined);
console.log('NFL combined panel initializes with empty matchup slate and without external dependencies');
