#!/usr/bin/env python3
"""Exact-image persistent installation, one-boot acceptance, commit, and rollback.
Uses an existing verified SSH connection. Never signals factory processes/reboots.
"""
import argparse,json,hashlib,shlex,time,io
from pathlib import Path
from run_v1_validation import Remote,manifest
from prepare_persistent import TARGETS,BINS
ROOT='/var/opt/supra-hud/v1';STATE='/tmp/supra-hud-v1'
def q(s):return shlex.quote(str(s))
def execute(a):
 files,kit_hash=manifest(a.kit);statefile=a.output/'installer.json'
 if a.phase=='preflight':a.output.mkdir(parents=True,exist_ok=False);s={'kit':kit_hash,'head':a.head,'phases':{},'applied':[]}
 else:s=json.loads(statefile.read_text());assert s['kit']==kit_hash and s['head']==a.head
 r=Remote(a.ssh_socket,a.head)
 def save():statefile.write_text(json.dumps(s,indent=2))
 def run(c,data=None):
  result=r.run(c,data);i=s.get('commands',0)+1;s['commands']=i
  (a.output/('%04d.stdout'%i)).write_bytes(result.stdout);(a.output/('%04d.stderr'%i)).write_bytes(result.stderr);save()
  if result.returncode:raise RuntimeError('Target command failed: '+c)
  return result.stdout
 def read(p):return run('cat '+q(p))
 def put(name,path,mode='700'):
  b=(a.kit/name).read_bytes();run('set -C; umask 077; cat > '+q(path),b);assert read(path)==b;run('chmod '+mode+' '+q(path))
 def current(which,version):assert read(TARGETS[which][0])==(a.kit/(which+'-'+version+'.cfg')).read_bytes()
 def mount(write):
  run('mount -u'+('w' if write else 'r')+' /fs/sda0');flags=run('df -g /fs/sda0');assert (b'rdonly' in flags)!=write
 def tx(which,action):return run(ROOT+'/supra-'+('startup' if which=='nav' else 'system')+'-transaction-qnx '+action+' '+ROOT+'/'+which+'-before.cfg '+ROOT+'/'+which+'-after.cfg')
 def marker():
  path='/tmp/supra-v1-boundary-'+str(time.time_ns())[-16:];run('set -C; cat > '+q(path),b'boot\n');s['boundary']=path;save()
 def absent_hook():
  for name in ['NavNBTEvoController','HmiMain3D']:
   p=r.run('slay -p '+name);assert p.returncode==1 and p.stdout.strip().isdigit();assert b'ff-experimental.so' not in run('pidin -p '+p.stdout.decode().strip()+' mem')
 try:
  if a.phase=='preflight':
   assert b'QNX hu-omap 6.5.0' in run('uname -a');absent_hook()
   for name in TARGETS:current(name,'before')
   m=json.loads((a.kit/'manifest.json').read_text())
   for path,digest in m['factory'].items():assert hashlib.sha256(read(path)).hexdigest()==digest
   # Inspect the exact live HMI library before any write. This dependency was not
   # captured during the earlier session; do not silently assume getter exports.
   from elftools.elf.elffile import ELFFile
   lib=read('/opt/sys/lib/libsys_someip.gpp.so.8');elf=ELFFile(io.BytesIO(lib));symbols={x.name for x in elf.get_section_by_name('.dynsym').iter_symbols() if x['st_shndx']!='SHN_UNDEF'}
   required=['_ZN6SomeIP14CSomeIPMessage15getBytesWrittenEv','_ZN6SomeIP14CSomeIPMessage8getBytesEv','_ZN6SomeIP14CSomeIPMessage21getDestinationAddressEv','_ZN6SomeIP22CSomeIPProtocolAdapter13doSendMessageERKSt8weak_ptrI21CSocketSenderReceiverI11CDispatcherS0_EERNS_14CSomeIPMessageE']
   assert set(required)<=symbols,'HMI dependency exports differ; no installation'
   s['hmi_library_sha256']=hashlib.sha256(lib).hexdigest();run('[ ! -e '+ROOT+' ]');s['phases']['preflight']=True
  elif a.phase=='install':
   assert s['phases'].get('preflight')
   for name in TARGETS:current(name,'before')
   run('umask 077; mkdir '+ROOT)
   for name in files:
    if name in ('supra-nav-start-qnx','supra-hmi-start-qnx'):continue
    put(name,ROOT+'/'+name,'600' if name.endswith(('.cfg','.bin')) else '700')
   try:
    mount(True)
    for name,target in [('supra-nav-start-qnx',TARGETS['nav'][2]),('supra-hmi-start-qnx',TARGETS['system'][2])]:put(name,target)
    for name in ['nav','system']:
     s['applied'].append(name);save();assert b'APPLY_VERIFIED' in tx(name,'apply');current(name,'after')
   finally:mount(False)
   s['phases']['install']=True
  elif a.phase=='arm':
   assert s['phases'].get('install')
   for name in TARGETS:current(name,'after')
   run(ROOT+'/supra-persistent-state-qnx arm');marker();s['phases']['arm']=True
  elif a.phase=='collect':
   for path in ['acceptance.json','worker.starts','worker.result','worker.stderr','last-result','active.jsonl','previous.jsonl','hook.log','resident.status']:
    result=r.run('cat '+STATE+'/'+path);(a.output/path).write_bytes(result.stdout);(a.output/(path+'.stderr')).write_bytes(result.stderr)
   s['phases']['collect']=True
  elif a.phase=='commit':
   assert s['phases'].get('arm') and all([a.navigation_return_confirmed,a.radio_return_confirmed,a.cleanup_confirmed,a.startup_confirmed])
   run('[ ! -e '+q(s['boundary'])+' ]');assert read(ROOT+'/consumed')==b'SUPRA-TRIAL-1\n'
   for name in TARGETS:current(name,'after')
   for name in ['NavNBTEvoController','HmiMain3D']:
    p=r.run('slay -p '+name);assert p.returncode==1 and p.stdout.strip().isdigit();assert b'ff-experimental.so' in run('pidin -p '+p.stdout.decode().strip()+' mem')
   for name,digest in files.items():
    path=TARGETS['nav'][2] if name=='supra-nav-start-qnx' else TARGETS['system'][2] if name=='supra-hmi-start-qnx' else ROOT+'/'+name
    assert hashlib.sha256(read(path)).hexdigest()==digest,'Installed release changed'
   heartbeat=read(STATE+'/heartbeat');time.sleep(1.1);assert read(STATE+'/heartbeat')!=heartbeat
   evidence=json.loads(read(STATE+'/acceptance.json'));assert not evidence['quarantined'] and evidence['worker_running'] and evidence['worker_starts']>=3 and evidence['clean_stops']>=2 and evidence['uptime_ms']>=300000
   for name in ['navigation','radio']:assert evidence[name+'_idle_commits']>=2 and evidence[name+'_active_commits']>=1
   frames=[json.loads(line).get('frame',0) for line in read(STATE+'/active.jsonl').splitlines()];assert max(frames)>=1200,'Five-minute resumed continuous run required'
   s['acceptance']=evidence;save();run(ROOT+'/supra-persistent-state-qnx commit');s['phases']['commit']=True
  elif a.phase=='disable':
   assert b'CLEAN' in run(ROOT+'/supra-resident-qnx --stop '+STATE);run(ROOT+'/supra-persistent-state-qnx disable');s['phases']['disable']=True
  elif a.phase=='rollback':
   # Restoring startup never claims to unload currently mapped libraries.
   result=r.run('[ ! -S '+STATE+'/factory.sock ]');
   if result.returncode:assert b'CLEAN' in run(ROOT+'/supra-resident-qnx --stop '+STATE)
   if r.run('[ -e '+ROOT+'/disabled ]').returncode:run(ROOT+'/supra-persistent-state-qnx disable')
   try:
    mount(True)
    for name in reversed(s['applied']):
     current_bytes=read(TARGETS[name][0])
     if current_bytes==(a.kit/(name+'-after.cfg')).read_bytes():assert b'ROLLBACK_VERIFIED' in tx(name,'rollback')
     current(name,'before')
   finally:mount(False)
   marker();s['phases']['rollback']=True
  elif a.phase=='verify-restored':
   assert s['phases'].get('rollback') and a.factory_normal;run('[ ! -e '+q(s['boundary'])+' ]')
   for name in TARGETS:current(name,'before')
   absent_hook();run('[ ! -e '+STATE+' ]');s['phases']['verify-restored']=True
  save();return s
 except Exception as e:s['error']=str(e);save();raise
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['preflight','install','arm','collect','commit','disable','rollback','verify-restored']);p.add_argument('--execute',action='store_true')
 for name in ['kit','output','ssh-socket']:p.add_argument('--'+name,type=Path)
 p.add_argument('--head',default='169.254.199.119')
 for name in ['navigation-return-confirmed','radio-return-confirmed','cleanup-confirmed','startup-confirmed','factory-normal']:p.add_argument('--'+name,action='store_true')
 a=p.parse_args()
 if not a.execute:print('Offline plan only: preflight, install unarmed, arm one boot, normal restart, continuous/nav/radio/return validation, commit; disable/rollback available.');raise SystemExit()
 if not all([a.kit,a.output,a.ssh_socket]):p.error('kit, output and ssh-socket required')
 print(json.dumps(execute(a),indent=2))
