#!/usr/bin/env node
'use strict';
// Inventory only: never reconstruct a pregame forecast or treat stats as bets.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const exists=p=>fs.existsSync(path.join(root,p));
const load=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const stats=exists('feed/nfl_player_stats.json')?load('feed/nfl_player_stats.json'):null;
const props=exists('feed/nfl_props.json')?load('feed/nfl_props.json'):null;
const forecastLedger='feed/nfl_prop_forecast_ledger.json';
const forecastArchive=exists(forecastLedger)?load(forecastLedger):null;
const archived='feed/nfl_prop_graded_snapshots.json';
const rows=exists(archived)?load(archived):null;
const validRows=Array.isArray(rows)?rows.length:0;
const forecasts=Array.isArray(forecastArchive?.forecasts)?forecastArchive.forecasts:[];
const forecastIds=new Set(forecasts.map(x=>x.forecast_id));
const forecastMarkets={};for(const x of forecasts)forecastMarkets[x.market]=(forecastMarkets[x.market]||0)+1;
const gradedIds=new Set((Array.isArray(rows)?rows:[]).map(x=>x.forecast_id));
const pendingForecasts=forecasts.filter(x=>!gradedIds.has(x.forecast_id)).length;
const quoteTimes=(Array.isArray(props?.odds)?props.odds:[]).map(x=>Date.parse(x.updated_at)).filter(Number.isFinite);
const newestQuote=quoteTimes.length?new Date(Math.max(...quoteTimes)).toISOString():null;
const distinctMarkets=[...new Set((Array.isArray(props?.odds)?props.odds:[]).map(x=>x.market).filter(Boolean))].sort();
const report={
 status:'RESEARCH_ONLY_NOT_BET_ELIGIBLE',
 generated_at:new Date().toISOString(),
 player_history_available:stats!==null,
 sportsbook_prop_snapshot_available:props!==null,
 sportsbook_prop_quote_count:Array.isArray(props?.odds)?props.odds.length:0,
 sportsbook_snapshot_at:props?.fetched_at||null,
 newest_sportsbook_quote_at:newestQuote,
 sportsbook_market_types:distinctMarkets,
 sportsbook_quote_age_minutes:newestQuote?Math.round((Date.now()-Date.parse(newestQuote))/60000):null,
 sportsbook_quotes_fresh_within_6h:newestQuote?Date.now()-Date.parse(newestQuote)<=21600000:false,
 archived_pregame_forecast_file_present:forecastArchive!==null,
 archived_pregame_forecast_count:forecasts.length,
 archived_pregame_unique_forecast_ids:forecastIds.size,
 archived_pregame_forecasts_by_market:forecastMarkets,
 archived_pregame_forecasts_awaiting_grading:pendingForecasts,
 archived_graded_prop_file_present:exists(archived),
 archived_graded_prop_rows:validRows,
 calibration_ready_for_execution:validRows>0,
 missing_requirements:[...(forecasts.length?[]:['Timestamped pregame model predictions with exact sportsbook lines']),...(validRows?[]:['Independently verified game-specific final player outcomes and exact-event grading']), 'Adequate chronological out-of-sample sample size and market-relative calibration before betting eligibility'],
 notes:['Historical player game logs are not pregame forecast archives','A current sportsbook snapshot is not a historical executable bet','No model hit rate, ROI or calibration is inferred from these inputs']
};
const dest=path.join(root,'reports','nfl_prop_readiness.json');
fs.mkdirSync(path.dirname(dest),{recursive:true});
fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
