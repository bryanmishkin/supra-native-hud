#!/usr/bin/env python3
"""Offline exact-image persistent installer kit; contains private config/profile."""
import argparse,json,hashlib,shutil,xml.etree.ElementTree as ET
from pathlib import Path
BINS=['supra-resident-qnx','supra-standalone-parked-qnx','libsupra-navigation-handoff-experimental.so','supra-nav-start-qnx','supra-hmi-start-qnx','supra-startup-transaction-qnx','supra-system-transaction-qnx','supra-persistent-state-qnx']
TARGETS={'nav':('/opt/nav/eceusa/bin/NavigationEceUsa.cfg','./NavNBTEvoController','/opt/nav/eceusa/bin/supra-nav-start-qnx','softrt_NAV','2'),'system':('/opt/sys/etc/starter.cfg','/opt/hmi/bin/zipped/HmiMain3D','/opt/hmi/bin/supra-hmi-start-qnx','interaction','17')}
def sha(b):return hashlib.sha256(b).hexdigest()
def patch(before,which):
 target,old,new,partition,number=TARGETS[which];root=ET.fromstring(before)
 found=[p for p in root.findall('./ProcessTable/Process') if p.findtext('Name')==old]
 if len(found)!=1:raise ValueError('Expected exactly one '+which+' process')
 p=found[0]
 if p.findtext('Partition')!=partition or p.findtext('Number')!=number or p.findtext('Args')!=p.findtext('ResArgs'):raise ValueError('Unexpected factory supervision contract')
 old=('<Name>'+old+'</Name>').encode();new=('<Name>'+new+'</Name>').encode()
 if before.count(old)!=1:raise ValueError('Ambiguous exact entry')
 after=before.replace(old,new);ET.fromstring(after);return after

def prepare(nav,system,build,profile,nav_exe,hmi_exe,out):
 out.mkdir(parents=True,exist_ok=False)
 for name,source in [('nav',nav),('system',system)]:
  b=source.read_bytes();a=patch(b,name);(out/(name+'-before.cfg')).write_bytes(b);(out/(name+'-after.cfg')).write_bytes(a)
 for name in BINS:shutil.copyfile(build/name,out/name)
 shutil.copyfile(profile,out/'supra-profile.bin')
 m={'schema':1,'mode':'persistent candidate with one-boot acceptance then explicit commit','factory':{'/opt/nav/eceusa/bin/NavNBTEvoController':sha(nav_exe.read_bytes()),'/opt/hmi/bin/zipped/HmiMain3D':sha(hmi_exe.read_bytes())},'sha256':{p.name:sha(p.read_bytes()) for p in sorted(out.iterdir())},'targets':TARGETS,'gates_not_yet_target_validated':['HMI factory gate','HMI SomeIP accessors','dual-path release and automatic return','resident capture across real boot'],'activation':'No arm or enabled token in kit; install does not enable drawing.'}
 (out/'manifest.json').write_text(json.dumps(m,indent=2));return m
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['nav','system','build','profile','nav-exe','hmi-exe','output']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();prepare(a.nav,a.system,a.build,a.profile,a.nav_exe,a.hmi_exe,a.output)
