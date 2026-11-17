#!/usr/bin/env python3
"""Prepare an exact one-use factory-started trial from a saved configuration.
Offline only. Produces no armed ticket and never contacts the vehicle.
"""
import argparse,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
OLD=b'<Name>./NavNBTEvoController</Name>'
NEW=b'<Name>/opt/nav/eceusa/bin/supra-boot-trial-gate-qnx</Name>'
TARGET='/opt/nav/eceusa/bin/NavigationEceUsa.cfg'
def prepare(source,out):
 before=source.read_bytes()
 if not 0<len(before)<512*1024 or before.count(OLD)!=1:raise ValueError('Expected exactly one captured controller entry')
 root=ET.fromstring(before);entries=[p for p in root.findall('./ProcessTable/Process') if p.findtext('Name')=='./NavNBTEvoController']
 if len(entries)!=1:raise ValueError('Ambiguous controller')
 p=entries[0]
 if p.findtext('Partition')!='softrt_NAV' or p.findtext('Args')!=p.findtext('ResArgs'):raise ValueError('Unexpected starter contract')
 if not any(x.findtext('Param')=='/opt/nav/eceusa/bin' for x in root.findall('./PackageTable/Package/StartEntryAction')):raise ValueError('Unverified working directory')
 after=before.replace(OLD,NEW);ET.fromstring(after)
 out.mkdir(parents=True,exist_ok=False);(out/'before.cfg').write_bytes(before);(out/'after.cfg').write_bytes(after)
 manifest={'target':TARGET,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),'change':'controller executable only; argv, working directory, environment and starter supervision preserved','armed':False,'installed':False,'draws_at_boot':False,'requires_current_target_byte_match':True,'must_not_stop_controller_pid':True}
 (out/'transaction.json').write_text(json.dumps(manifest,indent=2));return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('saved_config',type=Path);p.add_argument('output',type=Path);a=p.parse_args();print(json.dumps(prepare(a.saved_config,a.output),indent=2))
