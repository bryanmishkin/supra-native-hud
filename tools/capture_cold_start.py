#!/usr/bin/env python3
"""Read-only cold-start snapshot. No token changes, processes stopped or restarts.
Capture the first reachable boot BEFORE trying to recover the tachometer.
"""
import argparse,hashlib,json,time,datetime
from pathlib import Path
from run_v1_validation import Remote,manifest
from prepare_persistent import TARGETS
ROOT='/var/opt/supra-hud/v1';STATE='/tmp/supra-hud-v1'
FILES=['fault-first.json']+['fault-recent-%u.json'%i for i in range(4)]+['disabled','enabled','armed','consumed','last-gate-nav.status','last-gate-hmi.status','last-resident.status']
RAM=['admission.json','ready','heartbeat','acceptance.json','resident.status','resident.stderr','worker.starts','worker.result','worker.stderr','last-result','hook.log','active.jsonl','previous.jsonl','startup.pcap','failed-factory-request.bin','failed-factory-reply.bin']
def classify(data):
 disabled=data.get('disabled',b'').decode(errors='replace').strip()
 if disabled:return {'state':'persistently_disabled','reason':disabled,'clean_rpm_match':disabled=='clean I/O retry budget exhausted','action':'Preserve token/evidence; do not clear automatically.'}
 try:status=json.loads(data.get('acceptance.json',b''))
 except (ValueError,TypeError):status={}
 if status.get('quarantined'):return {'state':'runtime_quarantine','action':'Inspect first resident fault and cleanup result.'}
 if status.get('worker_running'):return {'state':'worker_reported_running','action':'Compare fresh heartbeat/frame advancement and visual HUD; this snapshot alone is not display proof.'}
 if status:return {'state':'resident_standby','available':status.get('available'),'action':'Inspect acknowledged nav/radio state and pending count; never infer idle from silence.'}
 return {'state':'no_runtime_status','action':'Compare gates, tokens, process maps, interface and resident startup stderr. Absence does not identify root cause.'}
def execute(a):
 a.output.mkdir(parents=True,exist_ok=False);r=Remote(a.ssh_socket,a.head);result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':a.head,'read_only':True,'commands':[]};data={}
 def save(): (a.output/'capture.json').write_text(json.dumps(result,indent=2)+'\n')
 def command(label,c):
  v=r.run(c);(a.output/(label+'.stdout')).write_bytes(v.stdout);(a.output/(label+'.stderr')).write_bytes(v.stderr);result['commands'].append({'label':label,'command':c,'exit_code':v.returncode});save();return v
 identity=command('identity','uname -a')
 if b'QNX hu-omap 6.5.0' not in identity.stdout:raise ValueError('Unexpected target identity; stopped')
 # Persistent fault reason is captured first, before any broader inspection.
 for n in FILES:data[n]=command('release-'+n,'cat '+ROOT+'/'+n).stdout
 for n in RAM:data[n]=command('ram-'+n,'cat '+STATE+'/'+n).stdout
 for label,c in [('release-list','ls -la '+ROOT),('runtime-list','ls -la '+STATE),('interfaces','ifconfig -a'),('routes','netstat -rn'),('connections','netstat -an'),('processes','pidin ar'),('mount','df -g /fs/sda0')]:command(label,c)
 for name in ['NavNBTEvoController','HmiMain3D','supra-resident-qnx','supra-standalone-parked-qnx']:
  v=command('pid-'+name,'slay -p '+name)
  for pid in v.stdout.split():
   if pid.isdigit():command('maps-'+name+'-'+pid.decode(),'pidin -p '+pid.decode()+' mem')
 expected,_=manifest(a.v1_kit);hashes={}
 for name,digest in expected.items():
  path=TARGETS['nav'][2] if name=='supra-nav-start-qnx' else TARGETS['system'][2] if name=='supra-hmi-start-qnx' else ROOT+'/'+name
  v=command('installed-'+name,'cat '+path);actual=hashlib.sha256(v.stdout).hexdigest() if v.returncode==0 else None;hashes[name]={'actual':actual,'gold_master':digest,'matches':actual==digest}
 for name,(path,*_) in TARGETS.items():
  v=command('startup-'+name,'cat '+path);hashes[name+'-startup']={'matches':v.returncode==0 and v.stdout==(a.v1_kit/(name+'-after.cfg')).read_bytes()}
 # Bounded second sample distinguishes stale files from a live process.
 time.sleep(2)
 for n in ['heartbeat','acceptance.json','active.jsonl']:command('second-'+n,'cat '+STATE+'/'+n)
 result['gold_master_comparison']=hashes;result['initial_classification']=classify(data);save();return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--v1-kit',type=Path);p.add_argument('--ssh-socket',type=Path);p.add_argument('--head',default='169.254.199.119');a=p.parse_args()
 if not a.execute:print(json.dumps({'network':False,'mode':'read-only first-boot snapshot','restarts':False,'clears_disabled':False}));raise SystemExit()
 if not all([a.output,a.v1_kit,a.ssh_socket]):p.error('output, original V1 kit and verified SSH socket required')
 print(json.dumps(execute(a),indent=2))
