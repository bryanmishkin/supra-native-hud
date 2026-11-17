#!/usr/bin/env python3
"""Explicit factory-started boot trial. Default is offline plan; never signals/reboots.
Normal head-unit restart is performed by the parked user between boot gates.
"""
import argparse,hashlib,json,subprocess,time,shlex,uuid
from pathlib import Path
from run_v1_validation import Remote,manifest
ROOT='/var/opt/supra-hud/boot-trial'
GATE='/opt/nav/eceusa/bin/supra-boot-trial-gate-qnx'
CFG='/opt/nav/eceusa/bin/NavigationEceUsa.cfg'
RAM='/tmp/supra-boot-rehearsal'
PHASES=['preflight','rehearse','configure','verify-baseline','arm','verify-hook','rollback','verify-restored']
DEPS={'preflight':[], 'rehearse':['preflight'], 'configure':['rehearse'], 'verify-baseline':['configure'], 'arm':['verify-baseline'], 'verify-hook':['arm'], 'rollback':['rehearse'], 'verify-restored':['rollback']}
def q(x):return shlex.quote(str(x))
def execute(a):
 files,kit_hash=manifest(a.kit);state=a.output/'boot-session.json'
 if a.phase=='preflight':a.output.mkdir(parents=True,exist_ok=False);s={'kit_sha256':kit_hash,'phases':{},'head':a.head}
 else:
  s=json.loads(state.read_text())
  if s['kit_sha256']!=kit_hash or s['head']!=a.head:raise ValueError('Kit or target changed')
 if any(not s['phases'].get(x) for x in DEPS[a.phase]):raise ValueError('Previous acceptance gate missing')
 if a.phase in ('arm','verify-baseline','verify-hook','verify-restored') and not a.factory_normal:raise ValueError('Fresh factory-function confirmation required')
 if a.phase=='rollback' and not s.get('configuration_attempted'):raise ValueError('No configuration attempt recorded')
 affected={a.phase};changed=True
 while changed:
  changed=False
  for phase,deps in DEPS.items():
   if phase not in affected and set(deps)&affected:affected.add(phase);changed=True
 if a.phase in ('configure','arm'):affected.update(['rollback','verify-restored'])
 for phase in affected:s['phases'].pop(phase,None)
 r=Remote(a.ssh_socket,a.head)
 def save():state.write_text(json.dumps(s,indent=2))
 def run(cmd,data=None,allow=False):
  result=r.run(cmd,data);idx=s.get('command_count',0)+1;s['command_count']=idx
  (a.output/('%03d-%s.stdout'%(idx,a.phase))).write_bytes(result.stdout);(a.output/('%03d-%s.stderr'%(idx,a.phase))).write_bytes(result.stderr)
  if result.returncode and not allow:raise RuntimeError('Target command failed; output preserved: '+cmd)
  return result
 def read(path):return run('cat '+q(path)).stdout
 def put(name,target,executable=False):
  data=(a.kit/name).read_bytes();run('set -C; umask 077; cat > '+q(target),data)
  if read(target)!=data:raise ValueError('Readback differs: '+target)
  run('chmod '+('700' if executable else '600')+' '+q(target))
 def pid():
  # QNX slay -p returns the number of matches, not conventional zero success.
  result=run('slay -p NavNBTEvoController',allow=True);p=result.stdout.decode().strip()
  if not p.isdigit() or result.returncode!=1:raise ValueError('Expected exactly one factory controller')
  args=run('pidin -p '+p+' ar').stdout
  if b'NavNBTEvoController' not in args:raise ValueError('Controller identity mismatch')
  return p
 def current(expected):
  if read(CFG)!=(a.kit/expected).read_bytes():raise ValueError('Current factory config differs; stop and inspect')
 def mark_boundary():
  marker='/tmp/supra-boot-boundary-'+uuid.uuid4().hex[:16]
  run('set -C; umask 077; cat > '+q(marker),b'normal-boot-boundary\n');s['boot_boundary']=marker;save()
 def stable_boot(previous,hook):
  marker=s.get('boot_boundary')
  if not marker or not marker.startswith('/tmp/supra-boot-boundary-'):raise ValueError('Missing boot-boundary evidence')
  run('[ ! -e '+q(marker)+' ]')
  p=pid()
  # Factory PIDs can repeat after reboot. RAM-sentinel loss proves the boundary.
  s['previous_controller_pid']=previous
  # Sustained check before drawing; no HUD writes are made during this interval.
  for i in range(25):
   if pid()!=p:raise ValueError('Controller changed during stabilization')
   mem=run('pidin -p '+p+' mem').stdout
   if (b'ff-experimental.so' in mem)!=hook:raise ValueError('Hook mapping does not match expected boot mode')
   if i!=24:time.sleep(5)
  return p
 try:
  if a.phase=='preflight':
   identity=run('uname -a').stdout
   if b'QNX hu-omap 6.5.0' not in identity or b'armle' not in identity:raise ValueError('Unexpected head unit')
   current('before.cfg');s['initial_pid']=pid();run('ls -ln '+q(CFG)+'; mount');s['backup_sha256']=hashlib.sha256(read(CFG)).hexdigest()
  elif a.phase=='rehearse':
   run('umask 077; mkdir '+RAM)
   for name in ['supra-startup-rehearsal-qnx','supra-boot-gate-rehearsal-qnx','fake-factory-qnx','libsupra-navigation-handoff-experimental.so']:put(name,RAM+'/'+name,True)
   for name,data in [('before',b'original\n'),('after',b'candidate\n'),('fixture.cfg',b'original\n')]:run('set -C; umask 077; cat > '+RAM+'/'+name,data)
   for action,expected in [('apply',b'candidate\n'),('rollback',b'original\n')]:
    result=run(RAM+'/supra-startup-rehearsal-qnx '+action+' '+RAM+'/before '+RAM+'/after').stdout
    if (action.upper()+'_VERIFIED').encode() not in result or read(RAM+'/fixture.cfg')!=expected:raise ValueError('Native transaction rehearsal failed')
   for mode in ['default','armed','consumed']:
    if mode=='armed':run('set -C; umask 077; cat > '+RAM+'/armed',b'SUPRA-BOOT-TRIAL-1\n')
    result=run(RAM+'/supra-boot-gate-rehearsal-qnx --config=original '+q('argument with spaces')).stdout
    if b'FAKE_FACTORY_ONLY' not in result or b'ARG=argument with spaces' not in result:raise ValueError('Gate fixture failed')
    if mode=='armed':
     if ('PRELOAD='+RAM+'/libsupra-navigation-handoff-experimental.so').encode() not in result:raise ValueError('Hook ticket not used')
    elif b'PRELOAD=none' not in result:raise ValueError('Default/consumed gate not passthrough')
  elif a.phase=='configure':
   current('before.cfg')
   run('umask 077; mkdir -p /var/opt/supra-hud; mkdir '+ROOT)
   for name in ['before.cfg','after.cfg','libsupra-navigation-handoff-experimental.so','supra-startup-transaction-qnx']:put(name,ROOT+'/'+name,name.endswith(('-qnx','.so')))
   put('supra-boot-trial-gate-qnx',GATE,True)
   s['preconfigure_pid']=pid();s['configuration_attempted']=True;save()
   result=run(ROOT+'/supra-startup-transaction-qnx apply '+ROOT+'/before.cfg '+ROOT+'/after.cfg').stdout
   if b'APPLY_VERIFIED' not in result:raise ValueError('Configuration apply not verified')
   current('after.cfg');mark_boundary()
  elif a.phase=='verify-baseline':
   current('after.cfg');s['baseline_pid']=stable_boot(s['preconfigure_pid'],False)
  elif a.phase=='arm':
   current('after.cfg')
   if pid()!=s['baseline_pid']:raise ValueError('Baseline process changed')
   for name,path in [('supra-boot-trial-gate-qnx',GATE),('libsupra-navigation-handoff-experimental.so',ROOT+'/libsupra-navigation-handoff-experimental.so')]:
    if read(path)!=(a.kit/name).read_bytes():raise ValueError('Installed trial file changed')
   run('[ ! -e '+ROOT+'/consumed ] && [ ! -e '+ROOT+'/disabled ] && [ ! -e '+ROOT+'/armed ]')
   mark_boundary();run('set -C; umask 077; cat > '+ROOT+'/armed',b'SUPRA-BOOT-TRIAL-1\n')
  elif a.phase=='verify-hook':
   current('after.cfg');run('[ ! -e '+ROOT+'/armed ]')
   if read(ROOT+'/consumed')!=b'SUPRA-BOOT-TRIAL-1\n':raise ValueError('Ticket consumption not verified')
   s['hook_pid']=stable_boot(s['baseline_pid'],True)
  elif a.phase=='rollback':
   # Config restoration does not unload a mapped library. Normal reboot follows.
   run('[ ! -S /tmp/supra-hud-boottrial/active.jsonl.handoff ]')
   s['prerollback_pid']=pid();save();result=run(ROOT+'/supra-startup-transaction-qnx rollback '+ROOT+'/before.cfg '+ROOT+'/after.cfg').stdout
   if b'ROLLBACK_VERIFIED' not in result:raise ValueError('Restore not verified')
   current('before.cfg');mark_boundary()
  elif a.phase=='verify-restored':
   current('before.cfg');s['restored_pid']=stable_boot(s['prerollback_pid'],False)
  s['phases'][a.phase]=True
 except Exception as error:
  s['phases'][a.phase]=False;s['last_error']=str(error);save();raise
 save();return s
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=PHASES);p.add_argument('--execute',action='store_true');p.add_argument('--kit',type=Path);p.add_argument('--output',type=Path);p.add_argument('--ssh-socket',type=Path);p.add_argument('--head',default='169.254.199.119');p.add_argument('--factory-normal',action='store_true');a=p.parse_args()
 if not a.execute:print(json.dumps({'phases':PHASES,'signals_or_reboots':False,'default_vehicle_io':False,'automatic_drawing':False}));raise SystemExit()
 if not all((a.kit,a.output,a.ssh_socket)):p.error('kit, output, ssh-socket required')
 print(json.dumps(execute(a),indent=2))
