#!/usr/bin/env python3
"""Audit saved TCP inventories across HUD states; offline, no payload publication.
Absence in a sampled recording is not proof an interface does not exist.
"""
import argparse,collections,json
from pathlib import Path

def audit(roots):
 records=[];seen=set();errors=[]
 for root in roots:
  for path in sorted(root.rglob('inventory.json')):
   obj=json.loads(path.read_text())
   for s in obj.get('streams',[]):
    inv=s.get('inventory',{});sha=s.get('sha256') or inv.get('sha256')
    key=(sha,tuple(s.get('flow',[])))
    if sha and key in seen:continue
    if sha:seen.add(key)
    if s.get('parse_error'):errors.append({'source':str(path),'error':s['parse_error']})
    for h in inv.get('headers',[]):
     records.append(dict(source=str(path),flow=s.get('flow'),stream_sha256=sha,**h))
 counts=collections.Counter();states=collections.defaultdict(set)
 for r in records:
  k=(r['service'],r['method'],r['message_type']);counts[k]+=r['count'];states[r['service']].add(r['source'])
 return dict(schema=1,offline_only=True,unique_streams=len(seen),errors=errors,
  services=[dict(service=hex(s),recording_inventories=len(states[s]),methods=[dict(method=hex(m),kind=k,count=n) for (ss,m,k),n in sorted(counts.items()) if ss==s]) for s in sorted(states)],
  records=records,limitations=['Saved TCP inventories only; UDP/MOST and unobserved time are outside coverage.','Service traffic does not prove a drawing surface or root framebuffer.','Records retain private local paths/endpoints; publish only reviewed derived results.'])
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('roots',type=Path,nargs='+');p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=audit(a.roots);a.output.write_text(json.dumps(r,indent=2));print(json.dumps({'streams':r['unique_streams'],'services':[x['service'] for x in r['services']],'parse_errors':len(r['errors'])}))
