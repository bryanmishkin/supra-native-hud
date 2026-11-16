#!/usr/bin/env python3
"""Offline validation ledger; evidence is tied to one kit and one car session.

No vehicle writes. Failed/missing gates never turn into an installation pass.
"""
import argparse,hashlib,json,uuid
from pathlib import Path
GATES={
 'identity':[], 'backup':['identity'], 'native_loader':['identity'],
 'isolated_hook':['native_loader'], 'headunit_rpm':['native_loader'],
 'native_display':['isolated_hook','headunit_rpm'], 'native_cleanup':['native_display'],
 'startup_review':['backup'], 'rollback_rehearsal':['startup_review'],
 'factory_hook':['native_cleanup','rollback_rehearsal'], 'navigation_yield':['factory_hook'],
 'radio_yield':['factory_hook'], 'disable_stop':['navigation_yield','radio_yield'],
 'factory_restore':['disable_stop'], 'restart_cycle':['factory_restore'],
 'startup_idle_policy':['restart_cycle'], 'duration_and_thresholds':['native_cleanup'],
 'install_v1':['startup_idle_policy','duration_and_thresholds']}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def create(root,kit):
 root.mkdir(parents=True,exist_ok=False)
 state={'schema':1,'session':uuid.uuid4().hex,'kit_sha256':sha(kit),'gates':{},'installation_ready':False}
 (root/'session.json').write_text(json.dumps(state,indent=2));return state

def record(root,kit,gate,evidence,passed,observation):
 p=root/'session.json';s=json.loads(p.read_text())
 if sha(kit)!=s['kit_sha256']:raise ValueError('Kit changed; start a new validation session')
 if gate not in GATES:raise ValueError('Unknown gate')
 if any(s['gates'].get(dep,{}).get('passed') is not True for dep in GATES[gate]):raise ValueError('Prerequisite not passed')
 for dep in GATES[gate]:
  row=s['gates'][dep];path=root/row['evidence']
  if not path.is_file() or sha(path)!=row['sha256']:raise ValueError('Prerequisite evidence changed')
 if not observation.strip():raise ValueError('Concrete observation required')
 if not evidence.is_file() or not evidence.stat().st_size:raise ValueError('Saved evidence required')
 # Re-recording any stage invalidates all descendants, including installation.
 affected={gate};changed=True
 while changed:
  changed=False
  for k,deps in GATES.items():
   if k not in affected and set(deps)&affected:affected.add(k);changed=True
 for k in affected:s['gates'].pop(k,None)
 saved=root/(gate+'-evidence'+evidence.suffix);saved.write_bytes(evidence.read_bytes())
 s['gates'][gate]={'passed':bool(passed),'evidence':saved.name,'sha256':sha(saved),'observation':observation}
 s['installation_ready']=all(s['gates'].get(k,{}).get('passed') is True for k in GATES)
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(s,indent=2));tmp.replace(p);return s

def verify(root,kit):
 s=json.loads((root/'session.json').read_text())
 if sha(kit)!=s['kit_sha256']:return False
 for row in s['gates'].values():
  p=root/row['evidence']
  if not p.is_file() or sha(p)!=row['sha256']:return False
 return s['installation_ready'] and all(s['gates'].get(k,{}).get('passed') is True for k in GATES)
if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
 for action in ('create','record','verify'):
  q=sub.add_parser(action);q.add_argument('session',type=Path);q.add_argument('kit',type=Path)
  if action=='record':q.add_argument('gate',choices=GATES);q.add_argument('evidence',type=Path);q.add_argument('--passed',action='store_true');q.add_argument('--observation',required=True)
 a=p.parse_args()
 if a.action=='create':print(json.dumps(create(a.session,a.kit)))
 elif a.action=='record':print(json.dumps(record(a.session,a.kit,a.gate,a.evidence,a.passed,a.observation)))
 else:print(json.dumps({'installation_ready':verify(a.session,a.kit)}))
