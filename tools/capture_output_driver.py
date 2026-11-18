#!/usr/bin/env python3
"""Offline-default, read-only output-driver capture with V1 preservation checks."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import capture_runtime as runtime
from consolidated_capture import Session
import collect_pip_router as router

GRAPHICS='/lib/graphics/omap5430'
BASELINE=Path(__file__).resolve().parents[1]/'docs/V1-BASELINE.json'

def inventory_names(text):
    names=text.splitlines()
    if len(names)>256: raise ValueError('Graphics inventory limit exceeded')
    if any(not re.fullmatch(r'[A-Za-z0-9_.+-]+',n) or n in ('.','..') for n in names):
        raise ValueError('Unsafe graphics inventory')
    return sorted(n for n in names if re.search(r'\.so(?:\.[A-Za-z0-9_.+-]+)?$|\.conf$',n))

def baseline_paths(expected):
    result={}
    for n,h in expected.items():
        path={'supra-hmi-start-qnx':'/opt/hmi/bin/supra-hmi-start-qnx',
              'supra-nav-start-qnx':'/opt/nav/eceusa/bin/supra-nav-start-qnx'}.get(n,'/var/opt/supra-hud/v1/'+n)
        result[path]=h
    result['/opt/nav/eceusa/bin/NavigationEceUsa.cfg']=expected['nav-after.cfg']
    result['/opt/sys/etc/starter.cfg']=expected['system-after.cfg']
    return result

def snapshot(s,label,expected):
    rows={}; faults={}
    for path,digest in baseline_paths(expected).items():
        p=s.file(path)
        rows[path]=bool(p and hashlib.sha256(p.read_bytes()).hexdigest()==digest)
    for name in ['fault-first.json']+['fault-recent-%d.json'%i for i in range(4)]:
        r=s.call('cat /var/opt/supra-hud/v1/'+name)
        faults[name]={'exit':r.returncode,'sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr':r.stderr.decode(errors='replace')}
        (s.root/(label+'-'+name)).write_bytes(r.stdout)
    for name in ('acceptance.json','heartbeat','resident.status'):
        r=s.call('cat /tmp/supra-hud-v1/'+name)
        (s.root/(label+'-'+name)).write_bytes(r.stdout)
    result={'component_matches':rows,'all_15_match':len(rows)==15 and all(rows.values()),'faults':faults}
    (s.root/(label+'.json')).write_text(json.dumps(result,indent=2))
    return result

def audit(root,report):
    failures=[]
    for path,row in report['files'].items():
        if row['status'] not in ('verified','reverified'):continue
        p=root/row['file']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']: failures.append(path)
    return failures

def run(a):
    s=Session(a); s.identity()
    expected=json.loads(BASELINE.read_text())['component_sha256']
    before=snapshot(s,'v1-before',expected)
    if not before['all_15_match']:raise ValueError('V1 baseline mismatch; snapshot saved, capture stopped')
    missing=[]
    r=s.call('ls -1 '+GRAPHICS)
    if r.returncode:raise ValueError('Graphics inventory unavailable')
    (s.root/'graphics-inventory.txt').write_bytes(r.stdout)
    names=inventory_names(r.stdout.decode())
    if not names:raise ValueError('Empty graphics inventory')
    extras=tuple(GRAPHICS+'/'+n for n in names if '.so' in n)
    configs=tuple(GRAPHICS+'/'+n for n in names if n.endswith('.conf'))
    commands=(('graphics-links','ls -l '+GRAPHICS),('native-displays','ls -l /dev/screen/0'),
              ('display-1','cat /dev/screen/0/dpy-1'),('display-2','cat /dev/screen/0/dpy-2'),
              ('interfaces','ifconfig -a'),('routes','netstat -rn'))
    # Preserve the original constants; this wrapper performs no vehicle mutations.
    original=(router.FILES,router.CONFIG_FILES)
    try:
        router.FILES=tuple(dict.fromkeys(router.FILES+extras))
        router.CONFIG_FILES=tuple(dict.fromkeys(router.CONFIG_FILES+configs))
        for label,cmd in commands:
            r=s.call(cmd);(s.root/(label+'.txt')).write_bytes(r.stdout)
            if r.returncode:missing.append(label)
        report=router.collect(a,session=s)
    finally:
        router.FILES,router.CONFIG_FILES=original
        after=snapshot(s,'v1-after',expected)
        s.report['v1_before']=before;s.report['v1_after']=after;s.persist()
    missing+=report.get('missing',[])
    if not after['all_15_match']:missing.append('V1 baseline changed')
    if before['faults']!=after['faults']:missing.append('Permanent fault records changed')
    missing+=['local hash mismatch:'+p for p in audit(s.root,s.report)]
    s.report.update(missing=sorted(set(missing)),capture_complete=not missing,
                    human_display_check_pending=True,larger_display_proven=False)
    s.persist();return s.report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    for n in ('head','local'):p.add_argument('--'+n,type=runtime.link_local)
    for n in ('known-hosts','socket','output'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if not a.execute:
        print(json.dumps({'remote_writes':False,'network':False,'restarts':False,'drawing':False,
          'capture':['15 V1 hashes before/after','permanent faults before/after','all graphics directory libraries and configurations','loaded driver dependency closure','current process maps and arguments','native display descriptors','LayerManager screens and surface 1056','interfaces and routes','local file hash audit'],
          'limits':'64 MiB/file, 512 MiB, 20 minutes; no raw framebuffer/device-memory reads',
          'success':'complete manifest plus owner final display check; does not prove larger windshield pixels'},indent=2));return 0
    if not all((a.head,a.local,a.known_hosts,a.output)):p.error('Verified addresses, known hosts and output required')
    r=run(a);print(json.dumps({'capture_complete':r['capture_complete'],'missing':r['missing']},indent=2))
    return 0 if r['capture_complete'] else 2
if __name__=='__main__':raise SystemExit(main())
