#!/usr/bin/env node
'use strict';
// Inventory only: never reconstruct a pregame forecast or treat stats as bets.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const exists=p=>fs.existsSync(path.join(root,p));
const load=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const stats=exists('feed/nfl_player_stats.json')?load('feed/nfl_player_stats.json'):null;
const props=exists('feed/nfl_props.json')?load('feed/nfl_props.json'):null;
const archived='feed/nfl_prop_graded_snapshots.json';
const rows=exists(archived)?load(archived):null;
const validRows=Array.isArray(rows)?rows.length:0;
const report={
 status:'RESEARCH_ONLY_NOT_BET_ELIGIBLE',
 generated_at:new Date().toISOString(),
 player_history_available:stats!==null,
 sportsbook_prop_snapshot_available:props!==null,
 sportsbook_prop_quote_count:Array.isArray(props?.odds)?props.odds.length:0,
 sportsbook_snapshot_at:props?.fetched_at||null,
 archived_graded_prop_file_present:exists(archived),
 archived_graded_prop_rows:validRows,
 calibration_ready_for_execution:validRows>0,
 missing_requirements:validRows?[]:['Timestamped pregame model probabilities paired with exact sportsbook lines and independently verified final player outcomes'],
 notes:['Historical player game logs are not pregame forecast archives','A current sportsbook snapshot is not a historical executable bet','No model hit rate, ROI or calibration is inferred from these inputs']
};
const dest=path.join(root,'reports','nfl_prop_readiness.json');
fs.mkdirSync(path.dirname(dest),{recursive:true});
fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
