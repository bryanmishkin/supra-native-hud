#!/usr/bin/env python3
"""Bounded RAM V2 test on the installed V1 reference car. Defaults to no network.
Never edits installed files/tokens/configuration; owner restarts iDrive to resume V1.
"""
import argparse,hashlib,json,shlex,time,uuid
from pathlib import Path
from run_v1_validation import Remote,manifest
from prepare_persistent import TARGETS
from prepare_v2_test import GOLD_KIT
ROOT='/var/opt/supra-hud/v1';STATE='/tmp/supra-hud-v1'
PHASES=('preflight','pause-v1','probe-boost','draw','draw-boost','yield','collect','verify-v1')
def q(x):return shlex.quote(str(x))
def execute(a):
 files,digest=manifest(a.kit);old,old_digest=manifest(a.kit/'v1-gold-master-kit')
 if old_digest!=GOLD_KIT:raise ValueError('V1 baseline mismatch')
 statefile=a.output/'v2-session.json'
 if a.phase=='preflight':a.output.mkdir(parents=True,exist_ok=False);s={'kit':digest,'head':a.head,'phases':{},'remote':'/tmp/supra-v2-'+uuid.uuid4().hex}
 else:
  s=json.loads(statefile.read_text())
  if s['kit']!=digest or s['head']!=a.head:raise ValueError('Kit/target changed')
 r=Remote(a.ssh_socket,a.head)
 def save():statefile.write_text(json.dumps(s,indent=2)+'\n')
 def run(command,data=None,allow_failure=False,timeout=50):
  v=r.run(command,data,timeout=timeout);i=s.get('commands',0)+1;s['commands']=i
  (a.output/('%04d.stdout'%i)).write_bytes(v.stdout);(a.output/('%04d.stderr'%i)).write_bytes(v.stderr);save()
  if v.returncode and not allow_failure:raise RuntimeError('Target command failed; evidence retained')
  return v
 def read(path):return run('cat '+q(path)).stdout
 def intact():
  for name,h in old.items():
   path=TARGETS['nav'][2] if name=='supra-nav-start-qnx' else TARGETS['system'][2] if name=='supra-hmi-start-qnx' else ROOT+'/'+name
   if hashlib.sha256(read(path)).hexdigest()!=h:raise ValueError('Installed V1 changed: '+name)
  for name,(path,*_) in TARGETS.items():
   if read(path)!=(a.kit/'v1-gold-master-kit'/(name+'-after.cfg')).read_bytes():raise ValueError('Startup configuration changed')
  if read(ROOT+'/enabled')!=b'SUPRA-PERSISTENT-1\n':raise ValueError('V1 not committed')
  run('[ ! -e '+ROOT+'/disabled ]');assert b'rdonly' in run('df -g /fs/sda0').stdout
 def hooks():
  for name in ['NavNBTEvoController','HmiMain3D']:
   v=run('slay -p '+name,allow_failure=True);pid=v.stdout.strip()
   if v.returncode!=1 or not pid.isdigit():raise ValueError('Factory process identity')
   if b'ff-experimental.so' not in run('pidin -p '+pid.decode()+' mem').stdout:raise ValueError('Factory hook missing')
 def quiet():
  if read(STATE+'/resident.status')!=b'STOPPED\n':raise ValueError('V1 resident not cleanly stopped')
  run('[ ! -S '+STATE+'/factory.sock ] && [ ! -S '+STATE+'/active.jsonl.handoff ]')
 def collect(label):
  d=a.output/label;d.mkdir(exist_ok=False)
  for n in ['acceptance.json','worker.result','worker.stderr','last-result','active.jsonl','previous.jsonl','hook.log','resident.status','heartbeat','startup.pcap']:
   v=run('cat '+STATE+'/'+n,allow_failure=True);(d/n).write_bytes(v.stdout);(d/(n+'.stderr')).write_bytes(v.stderr)
 try:
  if a.phase=='preflight':
   if b'QNX hu-omap 6.5.0' not in run('uname -a').stdout:raise ValueError('Wrong target')
   intact();hooks();health=json.loads(read(STATE+'/acceptance.json'))
   if health.get('quarantined') or not health.get('worker_running'):raise ValueError('Expected healthy running V1 baseline')
   collect('v1-before');run('umask 077; mkdir '+q(s['remote']))
   for name in ['supra-v2-test-qnx','supra-profile.bin']:
    data=(a.kit/name).read_bytes();path=s['remote']+'/'+name;run('set -C; umask 077; cat > '+q(path),data)
    if read(path)!=data:raise ValueError('Staged readback mismatch')
   run('chmod 700 '+q(s['remote']+'/supra-v2-test-qnx'))
   if not json.loads(run(q(s['remote']+'/supra-v2-test-qnx')+' --self-check').stdout).get('self_check'):raise ValueError('Loader self-check')
  elif a.phase=='pause-v1':
   if not s['phases'].get('preflight') or not a.guidance_stopped:raise ValueError('Preflight and current guidance/radio closed confirmation required')
   intact();hooks()
   if b'CLEAN' not in run(ROOT+'/supra-resident-qnx --stop '+STATE).stdout:raise ValueError('No CLEAN stop')
   # CLEAN precedes supervisor exit. Wait boundedly for its final status/socket.
   for _ in range(40):
    v=run('cat '+STATE+'/resident.status',allow_failure=True)
    if v.stdout==b'STOPPED\n':break
    time.sleep(.1)
   quiet();collect('v1-paused')
  elif a.phase in ('probe-boost','draw','draw-boost','yield'):
   if not s['phases'].get('pause-v1'):raise ValueError('V1 must be stopped cleanly first')
   if not a.guidance_stopped or not a.visual_cleanup_confirmed:raise ValueError('Current normal displays and closed factory overlays required')
   intact();hooks();quiet()
   if s.get('recovery_required'):raise ValueError('Prior cleanup uncertain; normal restart/recovery required')
   if a.phase=='draw-boost' and (not s['phases'].get('draw') or not s['phases'].get('probe-boost') or not a.candidate_boost_confirmed):raise ValueError('Passed layout/pressure probe and explicit experimental-boost confirmation required')
   attempt=s.get('attempts',0)+1;s['attempts']=attempt;save()
   exe=q(s['remote']+'/supra-v2-test-qnx')
   if a.phase=='probe-boost':
    v=run(exe+' --probe-boost-candidate 169.254.199.119 169.254.106.96',allow_failure=True)
    (a.output/('boost-probe-%02d.jsonl'%attempt)).write_bytes(v.stdout)
    rows=[json.loads(x) for x in v.stdout.splitlines()]
    if v.returncode or not rows or rows[-1].get('valid_pairs')!=40:raise ValueError('Pressure probe incomplete; layout-only test remains available')
   else:
    # Hooks already installed by V1 fall back to this same direct handoff socket
    # while their broker is absent. Archive only the known inactive journal.
    run('if [ -e '+STATE+'/active.jsonl ]; then [ -f '+STATE+'/active.jsonl ] && [ ! -L '+STATE+'/active.jsonl ] && mv '+STATE+'/active.jsonl '+q(s['remote']+'/prior-%02d.jsonl'%attempt)+'; fi')
    opt='--parked-v2-boost-candidate' if a.phase=='draw-boost' else '--parked-v2-guidance-stopped'
    cmd='unset SUPRA_HUD_BROKER_SOCKET SUPRA_HUD_HEARTBEAT; export SUPRA_HUD_DISABLE_FILE='+ROOT+'/disabled; '+exe+' '+opt+' '+q(s['remote']+'/supra-profile.bin')+' 169.254.199.119 169.254.106.96 160.48.199.96 vlan73 30 '+STATE+'/active.jsonl'
    s['recovery_required']=True;save()
    v=run(cmd,allow_failure=True,timeout=90);(a.output/('worker-%02d.json'%attempt)).write_bytes(v.stdout)
    collect('v2-%02d'%attempt)
    try:report=json.loads(v.stdout)
    except ValueError:s['recovery_required']=True;save();raise
    if not report.get('cleanup_verified') or not report.get('shared_instance_preserved'):s['recovery_required']=True;save();raise ValueError('Removal uncertain; restart recovery required')
    s['recovery_required']=False;save()
    expected='factory_navigation_request' if a.phase=='yield' else 'duration_complete'
    if v.returncode or report.get('reason')!=expected:raise ValueError('Run did not complete expected window/handoff')
  elif a.phase=='collect':collect('checkpoint-%04d'%s.get('commands',0))
  elif a.phase=='verify-v1':
   if not s['phases'].get('pause-v1') or not a.v1_visible:raise ValueError('Normal owner restart and visible V1 confirmation required')
   run('[ ! -e '+q(s['remote'])+' ]');intact();hooks()
   health=json.loads(read(STATE+'/acceptance.json'))
   if health.get('quarantined') or not health.get('worker_running'):raise ValueError('V1 not running normally')
   heartbeat=read(STATE+'/heartbeat');time.sleep(1.1)
   if heartbeat==read(STATE+'/heartbeat'):raise ValueError('V1 heartbeat not advancing')
   collect('v1-restored')
  s['phases'][a.phase]=True;save();return s
 except Exception as e:s['phases'][a.phase]=False;s['last_error']=str(e);save();raise
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=PHASES);p.add_argument('--execute',action='store_true')
 for n in ['kit','output','ssh-socket']:p.add_argument('--'+n,type=Path)
 p.add_argument('--head',default='169.254.199.119')
 for n in ['guidance-stopped','visual-cleanup-confirmed','candidate-boost-confirmed','v1-visible']:p.add_argument('--'+n,action='store_true')
 a=p.parse_args()
 if not a.execute:print(json.dumps({'phases':PHASES,'network':False,'installed_files_changed':False,'return_to_v1':'normal owner restart, then verify-v1'}));raise SystemExit()
 if not all([a.kit,a.output,a.ssh_socket]):p.error('kit/output/verified ssh-socket required')
 print(json.dumps(execute(a),indent=2))
