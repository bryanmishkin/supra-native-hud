#!/usr/bin/env python3
"""Build a measured V2 capability table from case evidence, not acknowledgments alone."""
import argparse,json
from pathlib import Path

def summarize(root):
 cases=[];bounds={}
 for result in sorted(root.glob('*/result.json')):
  r=json.loads(result.read_text());obsfile=result.parent/'observation.json'
  o=json.loads(obsfile.read_text()) if obsfile.exists() else {}
  steps=r.get('cleanup',[])
  if not isinstance(steps,list):continue # This reporter covers the B00E widget runner.
  clean=r.get('protocol_cleanup_ok') is True and isinstance(steps,list) and bool(steps) and all(x.get('ok') is True for x in steps)
  size=r.get('bitmap_dimensions');model=r.get('model_id');cell=r.get('cell')
  visible=o.get('distinct_custom_pixels')
  intact=o.get('all_border_edges_visible')
  row=dict(case=result.parent.name,model_id=model,cell=cell,bitmap_dimensions=size,
    protocol_cleanup=clean,distinct_custom_pixels=visible,unclipped=intact,
    windshield=o.get('windshield'),cluster=o.get('cluster'),observation_present=obsfile.exists(),
    root_surface_access=False)
  cases.append(row)
  if clean and visible is True and intact is True and o.get('windshield') is True and isinstance(size,list) and len(size)==2 and all(type(x) is int and x>0 for x in size):
   key=json.dumps([model,cell],sort_keys=True)
   bounds.setdefault(key,[]).append(size)
 return dict(cases=cases,verified_unclipped_windshield_bitmap_sizes=bounds,
   root_canvas_resolution=None,free_positioning_verified=False,
   caveat='Bitmap dimensions are not projected pixel dimensions. Missing observation is unknown, not failure. No root-surface access is inferred from a widget.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.write_text(json.dumps(summarize(a.root),indent=2)+'\n')
