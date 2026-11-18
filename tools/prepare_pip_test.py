#!/usr/bin/env python3
"""Offline-only packaging of an audited native PiP experiment and exact V1 reference."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from pip_trial import allocation,measured_support
from prepare_v2_test import ACCEPTED_V1_KIT
from run_v1_validation import manifest

def prepare(binary,audit,create,v1,out,capture,capture_audit):
    _,baseline=manifest(v1)
    if baseline!=ACCEPTED_V1_KIT:raise ValueError('Wrong V1 preservation baseline')
    a=json.loads(audit.read_text());sha=hashlib.sha256(binary.read_bytes()).hexdigest()
    if not a.get('static_gate_passed') or a.get('candidate',{}).get('sha256')!=sha:
        raise ValueError('Failed or stale ARM audit')
    ca=json.loads(capture_audit.read_text())
    if not ca.get('static_gate_passed') or ca.get('candidate',{}).get('sha256')!=hashlib.sha256(capture.read_bytes()).hexdigest():
        raise ValueError('Failed or stale passive capture audit')
    contract=measured_support((v1/'supra-profile.bin').read_bytes(),allocation(create.read_bytes()))
    out.mkdir(parents=True,exist_ok=False)
    shutil.copytree(v1,out/'v1-accepted-kit')
    for source,name in [(binary,'supra-pip-window-marker-qnx'),(audit,'arm-audit.json'),
                        (create,'create-response.bin'),(v1/'supra-profile.bin','supra-profile.bin'),
                        (capture,'supra-pip-passive-capture-qnx'),(capture_audit,'capture-audit.json')]:shutil.copy2(source,out/name)
    repo=Path(__file__).resolve().parents[1]
    shutil.copytree(repo/'vendor/ryseek-pip',out/'third-party/ryseek-pip')
    shutil.copy2(repo/'THIRD_PARTY_NOTICES.md',out/'THIRD_PARTY_NOTICES.md')
    data=dict(schema=1,kind='RAM-only experimental larger marker',seconds=30,
        v1_kit_sha256=baseline,contract=contract,car_tested=False,
        windshield_route_proven=False,automatic_v1_resume=False,
        sha256={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(out.rglob('*')) if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(data,indent=2)+'\n')
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['binary','audit','create-response','v1-kit','output','capture-binary','capture-audit']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=prepare(a.binary,a.audit,a.create_response,a.v1_kit,a.output,a.capture_binary,a.capture_audit)
    print(json.dumps({'packaged':str(a.output),'v1_kit_sha256':r['v1_kit_sha256'],'car_tested':False}))
