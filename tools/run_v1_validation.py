#!/usr/bin/env python3
"""One-session RAM acceptance runner. No factory config edits or restart.

Default prints the plan. Each execute phase is explicit; drawing requires a fresh
--guidance-stopped assertion. Only an existing verified SSH master is used.
"""
import argparse,hashlib,json,subprocess,shlex,uuid,ipaddress,stat
from pathlib import Path
PHASES=('preflight','stage','isolated','rpm','draw','yield','collect','remove')
def sha(b):return hashlib.sha256(b).hexdigest()
def q(s):return shlex.quote(str(s))
class Remote:
 def __init__(self,sock,head):
  if not sock.exists() or not stat.S_ISSOCK(sock.stat().st_mode):raise ValueError('Verified SSH master socket required')
  if not ipaddress.IPv4Address(head).is_link_local:raise ValueError('Expected ENET head-unit address')
  self.base=['ssh','-S',str(sock.resolve()),'-o','BatchMode=yes','-o','ProxyCommand=false','root@'+head]
  subprocess.run(self.base[:3]+['-O','check','root@'+head],check=True,capture_output=True,timeout=5)
 def run(self,command,data=None,timeout=50):
  return subprocess.run(self.base+[command],input=data,capture_output=True,timeout=timeout)
def manifest(kit):
 m=json.loads((kit/'manifest.json').read_text());files=m['sha256']
 for name,digest in files.items():
  if Path(name).name!=name or name in ('.','..') or not (kit/name).is_file():raise ValueError('Unsafe/missing package file')
  if sha((kit/name).read_bytes())!=digest:raise ValueError('Package hash mismatch: '+name)
 return files,sha((kit/'manifest.json').read_bytes())
def execute(a):
 kit=a.kit.resolve();files,kit_hash=manifest(kit);statefile=a.output/'runner-state.json'
 if a.phase=='preflight':
  a.output.mkdir(parents=True,exist_ok=False);s={'session':uuid.uuid4().hex,'kit_sha256':kit_hash,'head':a.head,'phases':{},'remote_dir':None}
 else:
  s=json.loads(statefile.read_text())
  if s['kit_sha256']!=kit_hash or s['head']!=a.head:raise ValueError('Kit or target changed')
 prerequisites={'preflight':(), 'stage':('preflight',), 'isolated':('stage',), 'rpm':('isolated',), 'draw':('isolated','rpm'), 'yield':('isolated','rpm','draw'), 'collect':('stage',), 'remove':('collect','draw','yield')}
 if any(s['phases'].get(x) is not True for x in prerequisites[a.phase]):raise ValueError('Required prior phase not passed')
 if a.phase in ('draw','yield') and not a.guidance_stopped:raise ValueError('Current stopped-guidance confirmation required')
 if a.phase=='remove' and not a.visual_cleanup_confirmed:raise ValueError('Visual removal/factory confirmation required')
 affected={a.phase};changed=True
 while changed:
  changed=False
  for phase,deps in prerequisites.items():
   if phase not in affected and set(deps)&affected:affected.add(phase);changed=True
 if a.phase in ('draw','yield'):affected.add('collect');affected.add('remove')
 for phase in affected:s['phases'].pop(phase,None)
 remote=Remote(a.ssh_socket,a.head)
 def save():
  temp=statefile.with_suffix('.tmp');temp.write_text(json.dumps(s,indent=2));temp.replace(statefile)
 def run(command,data=None,label=None):
  name=label or a.phase;r=remote.run(command,data)
  (a.output/(name+'.stdout')).write_bytes(r.stdout);(a.output/(name+'.stderr')).write_bytes(r.stderr)
  if r.returncode:raise RuntimeError('%s failed (%d); evidence saved'%(name,r.returncode))
  return r.stdout
 def require(*stages):
  if any(s['phases'].get(p) is not True for p in stages):raise ValueError('Required prior phase not passed: '+str(stages))
 def worker(journal):
  d=s['remote_dir'];return ' '.join(map(q,[d+'/supra-standalone-parked-qnx','--parked-guidance-stopped',d+'/supra-profile.bin','169.254.199.119','169.254.106.96','160.48.199.96','vlan73','30',journal]))
 try:
  if a.phase=='preflight':
   result=run('sh',data=(kit/'preflight-startup.sh').read_bytes())
   first=result.splitlines()[0]
   if b'QNX hu-omap 6.5.0' not in first or b'armle' not in first:raise ValueError('Unexpected target identity')
  elif a.phase=='stage':
   require('preflight');d='/dev/shmem/supra-v1-'+s['session'];s['remote_dir']=d;save();run('umask 077; mkdir '+q(d),label='mkdir')
   for name in files:
    body=(kit/name).read_bytes();run('set -C; umask 077; cat > '+q(d+'/'+name),data=body,label='upload-'+name)
    returned=run('cat '+q(d+'/'+name),label='readback-'+name)
    if sha(returned)!=files[name]:raise ValueError('Target readback mismatch: '+name)
    if name.endswith(('.sh','-qnx','.so')):run('chmod 700 '+q(d+'/'+name),label='mode-'+name)
  elif a.phase=='isolated':
   require('stage');d=s['remote_dir'];r=run(q(d+'/supra-standalone-parked-qnx')+' --self-check',label='native-loader')
   if json.loads(r).get('self_check') is not True:raise ValueError('Native self check failed')
   r=run(q(d+'/run-isolated-handoff-selftest.sh'))
   if b'PASS: isolated pre-send hook ABI and CLEAN handshake' not in r:raise ValueError('Isolated hook not verified')
  elif a.phase=='rpm':
   require('isolated');r=run(q(s['remote_dir']+'/supra-standalone-parked-qnx')+' --probe-rpm 169.254.199.119 169.254.106.96')
   rows=[json.loads(x) for x in r.splitlines()];last=rows[-1]
   if len(rows)!=41 or last.get('rpm_probe_passed') is not True or last.get('valid')!=40 or last.get('hud_writes')!=0:raise ValueError('RPM probe failed')
  elif a.phase in ('draw','yield'):
   require('isolated','rpm')
   if a.phase=='yield':require('draw')
   if not a.guidance_stopped:raise ValueError('Current stopped-guidance confirmation required')
   d=s['remote_dir'];attempt=s.setdefault('attempts',{}).get(a.phase,0)+1;s['attempts'][a.phase]=attempt;base=a.phase+'-%02d'%attempt;journal=d+'/'+base+'.jsonl';s.setdefault('remote_artifacts',[]).append(base+'.jsonl');save()
   if a.phase=='draw':r=run(worker(journal),label=base)
   else:
    command=worker(journal)+' > '+q(d+'/'+base+'-result.json')+' 2> '+q(d+'/'+base+'-worker.stderr')+' & child=$!; sleep 5; '+q(d+'/supra-hud-control-qnx')+' '+q(journal+'.handoff')+' > '+q(d+'/'+base+'-control.txt')+'; control=$?; wait "$child"; child_status=$?; cat '+q(d+'/'+base+'-result.json')+'; [ "$control" = 0 ] && [ "$child_status" = 0 ]'
    s['remote_artifacts'].extend(base+x for x in ('-result.json','-worker.stderr','-control.txt'));save();r=run(command,label=base)
   result=json.loads(r)
   if result.get('cleanup_verified') is not True or result.get('shared_instance_preserved') is not True:raise ValueError('Cleanup not verified')
   if a.phase=='draw' and result.get('reason')!='duration_complete':raise ValueError('Display run did not complete its window')
   if a.phase=='yield' and result.get('reason')!='factory_navigation_request':raise ValueError('No cooperative handoff')
  elif a.phase=='collect':
   require('stage');d=s['remote_dir']
   for name in s.get('remote_artifacts',[]):
    result=run('if [ -f '+q(d+'/'+name)+' ]; then cat '+q(d+'/'+name)+'; fi',label='collected-'+name)
    if name.endswith('.jsonl') and not result:raise ValueError('Missing worker journal; preserve target evidence')
  elif a.phase=='remove':
   require('collect')
   if not a.visual_cleanup_confirmed:raise ValueError('Current visual removal/factory confirmation required')
   if any(s['phases'].get(p) is not True for p in ('draw','yield')):raise ValueError('Do not erase failed-run evidence')
   d=s['remote_dir'];extra=s.get('remote_artifacts',[])
   guards=['[ ! -S '+q(d+'/'+name+'.handoff')+' ]' for name in extra if name.endswith('.jsonl')]
   command=' && '.join(guards+['rm -f '+' '.join(q(d+'/'+f) for f in list(files)+extra),'rmdir '+q(d)])
   run(command)
  s['phases'][a.phase]=True
 except Exception as error:
  s['phases'][a.phase]=False;s['last_error']=str(error);save();raise
 save();return s
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=PHASES);p.add_argument('--execute',action='store_true');p.add_argument('--kit',type=Path);p.add_argument('--output',type=Path);p.add_argument('--ssh-socket',type=Path);p.add_argument('--head',default='169.254.199.119');p.add_argument('--guidance-stopped',action='store_true');p.add_argument('--visual-cleanup-confirmed',action='store_true');a=p.parse_args()
 if not a.execute:print(json.dumps({'phases':PHASES,'factory_changes':False,'default_network':False,'installation_after_acceptance_only':True}));raise SystemExit()
 if not all((a.kit,a.output,a.ssh_socket)):p.error('kit, output and verified SSH socket required')
 print(json.dumps(execute(a),indent=2))
