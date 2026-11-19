#!/usr/bin/env python3
"""Summarize host rate-test evidence without claiming visible refresh proof."""
import argparse,json,statistics
from pathlib import Path

def summarize(root):
 rows=[]
 for path in sorted(root.glob('hz-*')):
  if not path.is_dir() or not (path/'hz-timing.json').exists():continue
  meta=json.loads((path/'hz-timing.json').read_text());f=path/'hz-frames.jsonl'
  frames=[json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []
  result=json.loads((path/'result.json').read_text()) if (path/'result.json').exists() else {}
  cleanup=result.get('cleanup',{});steps=result.get('cleanup_steps',[]);resources=cleanup.get('resources',[])
  clean=bool(steps and resources and all(s.get('acknowledged') is True for s in steps) and all(x.get('dispose_acknowledged') is True and x.get('post_dispose_check') is False for x in resources) and result.get('forward_cancelled') is True)
  cycles=sorted(x['cycle_seconds']*1000 for x in frames)
  elapsed=frames[-1]['posted']-frames[0]['posted'] if len(frames)>1 else 0
  passed=bool(len(frames)==meta['requested_hz']*meta['seconds'] and not any(x['missed_period'] for x in frames) and clean and result.get('status')=='awaiting_visual_verification')
  rows.append(dict(case=path.name,requested_hz=meta['requested_hz'],seconds=meta['seconds'],frames=len(frames),acknowledged_rate_hz=(len(frames)-1)/elapsed if elapsed>0 else None,median_cycle_ms=statistics.median(cycles) if cycles else None,max_cycle_ms=max(cycles) if cycles else None,deadline_misses=sum(x['missed_period'] for x in frames),protocol_cleanup=clean,host_schedule_pass=passed,error=result.get('error')))
 return dict(cases=rows,highest_completed_requested_hz=max((x['requested_hz'] for x in rows if x['host_schedule_pass']),default=None),verified_visible_maximum_hz=None,limitation='Host acknowledgments are not display frames; original video analysis and sustained repeat runs required.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args();print(json.dumps(summarize(a.root),indent=2))
