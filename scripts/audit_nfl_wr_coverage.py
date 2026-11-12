#!/usr/bin/env python3
"""Audit WR feed coverage by metric, team, and week; never fill missing values."""
import argparse,collections,json,pathlib
FIELDS=('targets','team_targets','receptions','receiving_yards','receiving_tds','offensive_snaps','routes_run','team_dropbacks','first_read_targets','team_first_read_targets','end_zone_targets','team_end_zone_targets')
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',default='feed/nfl_wr_opportunity.json');p.add_argument('--output',default='feed/nfl_wr_coverage.json');a=p.parse_args()
 data=json.loads(pathlib.Path(a.input).read_text());rows=data.get('games',[])
 if not rows:raise SystemExit('No player games for audit')
 groups=collections.defaultdict(list)
 for r in rows:groups[str(r.get('week','?'))+'|'+str(r.get('team','?'))].append(r)
 def coverage(rs):return {k:{'available':sum(r.get(k) is not None for r in rs),'total':len(rs),'pct':round(100*sum(r.get(k) is not None for r in rs)/len(rs),1)} for k in FIELDS}
 report={'season':data.get('season'),'source':data.get('source'),'player_games':len(rows),'metrics':coverage(rows),'team_weeks':{k:coverage(v) for k,v in sorted(groups.items())},'fully_covered':all(all(r.get(k) is not None for r in rows) for k in FIELDS)}
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
 print('Coverage:',json.dumps(report['metrics'],separators=(',',':')))
if __name__=='__main__':main()
