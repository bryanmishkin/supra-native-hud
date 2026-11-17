#!/usr/bin/env python3
"""Narrow repair for the captured Gold Master clean-RPM persistent disable only.
No connection without --execute. Does not reboot or start a process.
"""
import argparse,hashlib,json,shlex
from pathlib import Path
from run_v1_validation import Remote,manifest
from prepare_persistent import TARGETS
ROOT='/var/opt/supra-hud/v1'
REASON=b'clean I/O retry budget exhausted\n'
GOLD='84e5233be33e68bf305028cdb232d6e49f2f939af702ab69d44134768859078a'
REPLACEMENTS={'supra-resident-qnx':ROOT+'/supra-resident-qnx','supra-nav-start-qnx':TARGETS['nav'][2],'supra-hmi-start-qnx':TARGETS['system'][2]}
def eligible(capture,head):
 if capture.get('head')!=head or capture.get('read_only') is not True:return False
 c=capture.get('initial_classification',{});checks=capture.get('gold_master_comparison',{})
 return c.get('state')=='persistently_disabled' and c.get('clean_rpm_match') is True and len(checks)==15 and all(v.get('matches') is True for v in checks.values())
def execute(a):
 new,_=manifest(a.kit);old,old_hash=manifest(a.kit/'gold-master')
 if old_hash!=GOLD or set(REPLACEMENTS)!=set(new):raise ValueError('Unexpected kit baseline')
 capture=json.loads((a.capture/'capture.json').read_text())
 if set(capture.get('gold_master_comparison',{}))!=set(old)|{'nav-startup','system-startup'}:raise ValueError('Incomplete baseline evidence')
 if not eligible(capture,a.head) or (a.capture/'release-disabled.stdout').read_bytes()!=REASON:raise ValueError('Capture does not establish this exact repair condition')
 a.output.mkdir(parents=True,exist_ok=False);r=Remote(a.ssh_socket,a.head);s={'head':a.head,'replaced':[],'disabled_archived':False,'rollback_verified':False}
 def save():(a.output/'repair.json').write_text(json.dumps(s,indent=2)+'\n')
 def run(c,data=None):
  v=r.run(c,data);i=s.get('commands',0)+1;s['commands']=i;(a.output/('%03d.stdout'%i)).write_bytes(v.stdout);(a.output/('%03d.stderr'%i)).write_bytes(v.stderr);save()
  if v.returncode:raise RuntimeError('Target command failed; retain repair log')
  return v.stdout
 def read(path):return run('cat '+shlex.quote(path))
 def mount(write):
  run('mount -u'+('w' if write else 'r')+' /fs/sda0');assert (b'rdonly' in run('df -g /fs/sda0'))!=write
 def replace(path,data,rollback=False):
  tmp=path+('.cold-start-rollback' if rollback else '.cold-start-new');run('set -C; umask 077; cat > '+shlex.quote(tmp),data)
  if read(tmp)!=data:raise ValueError('Staging readback mismatch')
  run('chmod 700 '+shlex.quote(tmp));run('mv '+shlex.quote(tmp)+' '+shlex.quote(path))
  if read(path)!=data:raise ValueError('Installed readback mismatch')
 if b'QNX hu-omap 6.5.0' not in run('uname -a'):raise ValueError('Wrong target')
 if read(ROOT+'/disabled')!=REASON:raise ValueError('Current reason changed')
 if read(ROOT+'/enabled')!=b'SUPRA-PERSISTENT-1\n':raise ValueError('Persistence state changed')
 run('[ ! -S /tmp/supra-hud-v1/factory.sock ] && [ ! -S /tmp/supra-hud-v1/active.jsonl.handoff ]')
 for proc in ['supra-resident-qnx','supra-standalone-parked-qnx']:
  v=r.run('slay -p '+proc)
  if v.stdout.strip() or v.returncode not in (0,1):raise ValueError('Cannot establish stopped app: '+proc)
 for name,digest in old.items():
  path=REPLACEMENTS.get(name,ROOT+'/'+name)
  if hashlib.sha256(read(path)).hexdigest()!=digest:raise ValueError('Installed baseline changed: '+name)
 for name,(path,*_) in TARGETS.items():
  if read(path)!=(a.kit/'gold-master'/(name+'-after.cfg')).read_bytes():raise ValueError('Startup configuration changed')
 backup=ROOT+'/disabled.before-cold-start-fix';run('[ ! -e '+backup+' ]')
 try:
  mount(True)
  for name,path in REPLACEMENTS.items():
   s['replaced'].append(name);save();replace(path,(a.kit/name).read_bytes())
  mount(False)
  # Clear ONLY the proven legacy clean-input latch after verified new files.
  if read(ROOT+'/disabled')!=REASON:raise ValueError('Disable reason changed during repair')
  run('mv '+ROOT+'/disabled '+backup);s['disabled_archived']=True;save();run('sync')
  s['status']='patched; owner normal restart and cold-cycle validation still required';save()
 except Exception as e:
  s['error']=str(e);save()
  try:
   if s['disabled_archived']:run('set -C; umask 077; cat > '+ROOT+'/disabled',REASON)
   mount(True)
   for name in reversed(s['replaced']):replace(REPLACEMENTS[name],(a.kit/'gold-master'/name).read_bytes(),rollback=True)
   s['rollback_verified']=True;save()
  finally:mount(False)
  raise
 return s
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
 for n in ['kit','capture','output','ssh-socket']:p.add_argument('--'+n,type=Path)
 p.add_argument('--head',default='169.254.199.119');a=p.parse_args()
 if not a.execute:print('Offline plan only. Requires exact clean-RPM disable capture, original Gold Master hashes and stopped app. Replaces resident/two gates, archives only that disable reason, preserves enable/configs. No restart.');raise SystemExit()
 if not all([a.kit,a.capture,a.output,a.ssh_socket]):p.error('kit, first capture, new output and verified SSH socket required')
 print(json.dumps(execute(a),indent=2))
