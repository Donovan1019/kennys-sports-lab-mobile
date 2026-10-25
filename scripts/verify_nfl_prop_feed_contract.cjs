#!/usr/bin/env node
'use strict';
// Check actual existing upstream/downstream data contracts without manufacturing predictions.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const exists=p=>fs.existsSync(path.join(root,p));
const feed=exists('feed/nfl_props.json')?read('feed/nfl_props.json'):{};
const odds=Array.isArray(feed.odds)?feed.odds:[];
const valid=x=>x.event_id&&x.player&&x.market&&x.bookmaker&&Number.isInteger(x.price)&&Number.isFinite(Date.parse(x.updated_at))&&Number.isFinite(Date.parse(x.commence_time));
const bad=odds.filter(x=>!valid(x)).length;
const marketCounts={};for(const x of odds)marketCounts[x.market]=(marketCounts[x.market]||0)+1;
const paired=new Map();
for(const x of odds){if(!Number.isFinite(x.point)||!['Over','Under'].includes(x.selection))continue;const k=[x.event_id,x.player,x.market,x.point,x.bookmaker].join('|');const p=paired.get(k)||new Set();p.add(x.selection);paired.set(k,p)}
const twoWay=[...paired.values()].filter(x=>x.has('Over')&&x.has('Under')).length;
const result={status:'RESEARCH_ONLY',quote_count:odds.length,malformed_quote_rows:bad,markets:marketCounts,two_way_player_line_book_quotes:twoWay,archived_forecast_inbox_present:exists('feed/nfl_prop_forecast_inbox.json'),verified_outcomes_present:exists('feed/nfl_prop_verified_outcomes.json'),ready_for_automatic_accuracy:false,notes:['Quotes are not model forecasts','Two-way line pairs do not prove an executable bet or pregame model prediction','Missing pregame export and verified outcomes cannot be synthesized']};
fs.mkdirSync(path.join(root,'reports'),{recursive:true});
fs.writeFileSync(path.join(root,'reports','nfl_prop_feed_contract.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
