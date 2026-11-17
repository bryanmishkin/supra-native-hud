#!/usr/bin/env python3
"""Prepare audited RAM-only V2 trial alongside a pinned V1 rollback kit. No network."""
import argparse,hashlib,json,shutil
from pathlib import Path
from run_v1_validation import manifest
GOLD_KIT='84e5233be33e68bf305028cdb232d6e49f2f939af702ab69d44134768859078a'
def prepare(binary,audit,v1,out):
 files,digest=manifest(v1)
 if digest!=GOLD_KIT:raise ValueError('Expected preserved reference V1 Gold Master kit')
 sha=hashlib.sha256(binary.read_bytes()).hexdigest();a=json.loads(audit.read_text())
 if not a.get('static_gate_passed') or a.get('candidate',{}).get('sha256')!=sha:raise ValueError('Missing/failed/stale ARM executable audit')
 out.mkdir(parents=True,exist_ok=False);shutil.copytree(v1,out/'v1-gold-master-kit');shutil.copyfile(binary,out/'supra-v2-test-qnx');shutil.copyfile(v1/'supra-profile.bin',out/'supra-profile.bin');shutil.copyfile(audit,out/'v2-audit.json')
 data={'schema':1,'mode':'RAM-only bounded V2 trial; installed V1 files never replaced','v1_kit_sha256':digest,'sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['supra-v2-test-qnx','supra-profile.bin','v2-audit.json']},'live_boost':'candidate 4205/4201; unvalidated under load','car_tested':False}
 (out/'manifest.json').write_text(json.dumps(data,indent=2)+'\n');return data
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['binary','audit','v1-kit','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();print(json.dumps(prepare(a.binary,a.audit,a.v1_kit,a.output),indent=2))
