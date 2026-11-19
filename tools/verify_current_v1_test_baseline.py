#!/usr/bin/env python3
"""Offline verifier for read-only pre/post captures of the 19 November V1 install.

Prints fixed read commands but never connects, writes target files, stops V1 or
installs anything. Captures must include 13 component files and 2 live configs.
"""
import argparse, hashlib, json
from pathlib import Path

DOCS=Path(__file__).resolve().parents[1]/'docs'
ROOT='/var/opt/supra-hud/v1'
CURRENT_RESIDENT='78d463e60e399c299aaf38d608d3fd64593c0863cfd7ea88492eba730bc4e0c3'

def contract():
    baseline=json.loads((DOCS/'V1-BASELINE.json').read_text())
    recovery=json.loads((DOCS/'V1-CURRENT-RECOVERY.json').read_text())
    if baseline['baseline']!='v1-baseline-2026-11-18' or recovery['baseline']!=baseline['baseline']:
        raise ValueError('Baseline lineage changed: review required')
    if recovery['supervisor_override_sha256']!=CURRENT_RESIDENT or recovery['worker_and_startup_unchanged'] is not True:
        raise ValueError('Current recovery contract changed: review required')
    hashes=dict(baseline['component_sha256'])
    if len(hashes)!=13:raise ValueError('Unexpected component inventory')
    hashes['supra-resident-qnx']=CURRENT_RESIDENT
    paths={name:ROOT+'/'+name for name in hashes}
    paths['supra-hmi-start-qnx']='/opt/hmi/bin/supra-hmi-start-qnx'
    paths['supra-nav-start-qnx']='/opt/nav/eceusa/bin/supra-nav-start-qnx'
    for label,path,source in (
        ('installed-nav.cfg','/opt/nav/eceusa/bin/NavigationEceUsa.cfg','nav-after.cfg'),
        ('installed-system.cfg','/opt/sys/etc/starter.cfg','system-after.cfg')):
        hashes[label]=hashes[source];paths[label]=path
    return hashes,paths

def verify(directory):
    hashes,paths=contract();rows=[]
    for name,expected in hashes.items():
        p=directory/name
        if not p.is_file():raise ValueError('Missing captured file: '+name)
        actual=hashlib.sha256(p.read_bytes()).hexdigest()
        if actual!=expected:raise ValueError('Current V1 mismatch: '+name)
        rows.append(dict(name=name,remote_path=paths[name],sha256=actual))
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pre',type=Path);p.add_argument('--post',type=Path)
    p.add_argument('--read-plan',action='store_true')
    a=p.parse_args();hashes,paths=contract()
    if a.read_plan:
        print(json.dumps({'network_executed':False,'captures':[dict(local_name=n,command='cat '+v,sha256=hashes[n])for n,v in paths.items()]},indent=2));return
    if a.pre is None:p.error('Supply --pre capture directory or --read-plan')
    before=verify(a.pre);after=verify(a.post)if a.post else None
    if after is not None and before!=after:raise ValueError('Pre/post mismatch')
    print(json.dumps(dict(files_verified=len(before),current_resident_sha256=CURRENT_RESIDENT,
        post_verified=after is not None,pre_post_identical=after is not None,
        runtime_health_verified=False,visual_restoration_verified=False,files=before),indent=2))
if __name__=='__main__':main()
