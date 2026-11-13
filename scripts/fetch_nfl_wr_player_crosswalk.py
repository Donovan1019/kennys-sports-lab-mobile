#!/usr/bin/env python3
"""Fetch verified nflverse player crosswalk. No name-only player matching.
nflverse-players components release: players_pfr.rds, updated by nflverse.
"""
import argparse,csv,io,pathlib,urllib.request
URL="https://github.com/nflverse/nflverse-players/releases/download/players_components/players_pfr.rds"
def main():
 p=argparse.ArgumentParser();p.add_argument("--output",default="data/nfl_wr_verified/pfr_gsis_crosswalk.csv");a=p.parse_args()
 import pyreadr
 req=urllib.request.Request(URL,headers={"User-Agent":"KSL-WR/1.0"})
 with urllib.request.urlopen(req,timeout=45) as response:raw=response.read(15_000_000)
 if len(raw)<100:raise SystemExit("Empty nflverse crosswalk release")
 from tempfile import NamedTemporaryFile
 with NamedTemporaryFile(suffix=".rds") as tmp:
  tmp.write(raw);tmp.flush()
  frame=next(iter(pyreadr.read_r(tmp.name).values()))
 fields=set(frame.columns)
 pfr=next((x for x in ("pfr_id","pfr_player_id","pfr_id_player") if x in fields),None)
 gsis=next((x for x in ("gsis_id","player_id") if x in fields),None)
 if not pfr or not gsis:raise SystemExit("Unexpected nflverse crosswalk schema: "+str(sorted(fields)))
 mapping={};ambiguous=set()
 for row in frame[[pfr,gsis]].itertuples(index=False,name=None):
  a,b=(str(v).strip() if v is not None else "" for v in row)
  if not a or not b or a.lower()=="nan" or b.lower()=="nan":continue
  if a in mapping and mapping[a]!=b:ambiguous.add(a)
  else:mapping[a]=b
 for a in ambiguous:mapping.pop(a,None)
 if len(mapping)<100:raise SystemExit("Crosswalk coverage too small")
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open("w",newline="") as f:
  w=csv.DictWriter(f,fieldnames=["pfr_id","gsis_id"]);w.writeheader()
  for key,value in sorted(mapping.items()):w.writerow({"pfr_id":key,"gsis_id":value})
 print("Verified PFR->GSIS IDs:",len(mapping),"ambiguous rejected:",len(ambiguous))
if __name__=="__main__":main()
