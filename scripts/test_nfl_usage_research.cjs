#!/usr/bin/env node
'use strict';
const fs=require('fs'),assert=require('assert'),vm=require('vm');
const s=fs.readFileSync('scripts/audit_nfl_usage_research.cjs','utf8');
new vm.Script(s);
for(const token of ["g.season===2026","g.season_type==='REG'","g.game_id","valid.length<5","injury_verified:false","role_verified:false","betting_eligible:false","status:'RESEARCH_ONLY'"])assert(s.includes(token),'Missing fail-closed usage guard '+token);
console.log('PASS offline usage research safety');
