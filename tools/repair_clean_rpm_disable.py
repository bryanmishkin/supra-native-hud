#!/usr/bin/env python3
"""Narrow repair for the captured Gold Master clean-RPM persistent disable only.
No connection without --execute. Does not reboot or start a process.
"""
import argparse,hashlib,json,shlex,socket,struct,subprocess,uuid
from pathlib import Path
from run_v1_validation import Remote,manifest
from prepare_persistent import TARGETS
ROOT='/var/opt/supra-hud/v1'
REASON=b'clean I/O retry budget exhausted\n'
GOLD='84e5233be33e68bf305028cdb232d6e49f2f939af702ab69d44134768859078a'
REPLACEMENTS={'supra-resident-qnx':ROOT+'/supra-resident-qnx','supra-nav-start-qnx':TARGETS['nav'][2],'supra-hmi-start-qnx':TARGETS['system'][2]}
def eligible(capture,head,factory_close=False):
 if capture.get('head')!=head or capture.get('read_only') is not True:return False
 c=capture.get('initial_classification',{});checks=capture.get('gold_master_comparison',{})
 return c.get('state')=='persistently_disabled' and (c.get('reason')=='factory transport closed' if factory_close else c.get('clean_rpm_match') is True) and len(checks)==15 and all(v.get('matches') is True for v in checks.values())
def check_empty_pool(remote):
 # Read-only method 2 through the already verified SSH master; never creates a session.
 base=remote.base[:-1];target=remote.base[-1];forward='127.0.0.1:33053:160.48.199.96:30502'
 subprocess.run(base+['-O','forward','-L',forward,target],capture_output=True,check=True,timeout=5)
 rows=[]
 def exact(sock,n):
  b=b''
  while len(b)<n:
   part=sock.recv(n-len(b))
   if not part:raise RuntimeError('Presence query EOF')
   b+=part
  return b
 try:
  with socket.create_connection(('127.0.0.1',33053),3) as sock:
   sock.settimeout(3)
   for seq,rid in enumerate(range(0x1000000,0x100000a),1):
    body=struct.pack('>IIB',200,rid,1);sock.sendall(struct.pack('>HHIHHBBBB',0xb006,2,len(body)+8,0x5348,seq,1,1,0,0)+body)
    for _ in range(32):
     h=exact(sock,16);svc,m,n,client,session,pv,iv,kind,rc=struct.unpack('>HHIHHBBBB',h)
     if not 8<=n<=65544:raise ValueError('Presence response length')
     body=exact(sock,n-8)
     if svc==0xffff:continue
     if (svc,m,client,session,pv,iv,kind,rc)!=(0xb006,2,0x5348,seq,1,1,128,0) or body!=b'\x00':raise ValueError('Pool occupied or unverified; retain disable')
     rows.append({'id':hex(rid),'present':False});break
    else:raise ValueError('No correlated presence reply')
 finally:subprocess.run(base+['-O','cancel','-L',forward,target],capture_output=True,check=True,timeout=5)
 return rows

def execute(a):
 factory_close=getattr(a,'factory_close_recovery',False);reason=b'factory transport closed\n' if factory_close else REASON
 new,_=manifest(a.kit);old,old_hash=manifest(a.kit/'gold-master')
 if old_hash!=GOLD or set(REPLACEMENTS)!=set(new):raise ValueError('Unexpected kit baseline')
 capture=json.loads((a.capture/'capture.json').read_text())
 if set(capture.get('gold_master_comparison',{}))!=set(old)|{'nav-startup','system-startup'}:raise ValueError('Incomplete baseline evidence')
 if not eligible(capture,a.head,factory_close) or (a.capture/'release-disabled.stdout').read_bytes()!=reason:raise ValueError('Capture does not establish this exact repair condition')
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
 if read(ROOT+'/disabled')!=reason:raise ValueError('Current reason changed')
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
 if factory_close:s['before_pool']=check_empty_pool(r);save()
 backup=ROOT+'/disabled.before-cold-start-fix-'+uuid.uuid4().hex[:12];s['disable_backup']=backup;save();run('[ ! -e '+backup+' ]')
 try:
  mount(True)
  for name,path in REPLACEMENTS.items():
   s['replaced'].append(name);save();replace(path,(a.kit/name).read_bytes())
  mount(False)
  # Clear ONLY the proven legacy clean-input latch after verified new files.
  if read(ROOT+'/disabled')!=reason:raise ValueError('Disable reason changed during repair')
  if factory_close:s['pre_enable_pool']=check_empty_pool(r);save()
  run('mv '+ROOT+'/disabled '+backup);s['disabled_archived']=True;save();run(ROOT+'/supra-resident-qnx --sync-state')
  s['status']='patched; owner normal restart and cold-cycle validation still required';save()
 except Exception as e:
  s['error']=str(e);save()
  try:
   if s['disabled_archived']:run('set -C; umask 077; cat > '+ROOT+'/disabled',reason)
   mount(True)
   for name in reversed(s['replaced']):replace(REPLACEMENTS[name],(a.kit/'gold-master'/name).read_bytes(),rollback=True)
   s['rollback_verified']=True;save()
  finally:mount(False)
  raise
 return s
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--factory-close-recovery',action='store_true',help='Exact factory transport closed latch only; requires fresh empty-pool verification twice')
 for n in ['kit','capture','output','ssh-socket']:p.add_argument('--'+n,type=Path)
 p.add_argument('--head',default='169.254.199.119');a=p.parse_args()
 if not a.execute:print('Offline plan only. Requires exact clean-RPM disable capture, original Gold Master hashes and stopped app. Replaces resident/two gates, archives only that disable reason, preserves enable/configs. No restart.');raise SystemExit()
 if not all([a.kit,a.capture,a.output,a.ssh_socket]):p.error('kit, first capture, new output and verified SSH socket required')
 print(json.dumps(execute(a),indent=2))
