#!/usr/bin/env python3
import sys,socket,subprocess,json,time,signal,struct,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ric_shared_trial import SharedSession,SharedDrawingTrial,allocation_from_reply
from ric_live_trial import TcpExchange
from ric_graph import decode_graph_body,encode_description_body
parser=argparse.ArgumentParser(description='Live-verified shared road-icon marker test; requires stopped factory guidance.')
parser.add_argument('--execute',action='store_true')
parser.add_argument('--bitmap-bgra',type=Path,help='Optional 150x36 opaque BGRA test frame')
parser.add_argument('--guidance-stopped',action='store_true',help='Operator confirmed guidance and selector stopped')
parser.add_argument('--window-seconds',type=int,choices=range(1,16),default=15)
parser.add_argument('--create-response',type=Path)
parser.add_argument('--support-stream',type=Path)
parser.add_argument('--ssh-socket',type=Path)
parser.add_argument('--head')
parser.add_argument('--output',type=Path)
args=parser.parse_args()
if not args.execute:
 print('Offline plan: confirmed shared profile, free bitmap pool, RLE32 road-icon marker, 15 seconds, withdraw references, delete only uploaded bitmap, check absence. Requires current verified SSH master and stopped guidance. Never disposes factory instance.');sys.exit(0)
if not all((args.create_response,args.support_stream,args.ssh_socket,args.head,args.output)):parser.error('All file/connection/output arguments required')
if args.bitmap_bgra and not args.guidance_stopped:parser.error('Custom frames require --guidance-stopped')
custom = args.bitmap_bgra.read_bytes() if args.bitmap_bgra else None
if custom is not None and (len(custom)!=150*36*4 or any(x!=255 for x in custom[3::4])):parser.error('Expected exactly 150x36 opaque BGRA')
import ipaddress
ipaddress.IPv4Address(args.head)
root=args.output;root.mkdir(parents=True,exist_ok=False)
a=allocation_from_reply(args.create_response.read_bytes()[16:])
assert {17,29,34}.issubset(a['models'])
# Reuse only the measured factory support-model field values, with negotiated
# high-slot model IDs. Never replay a captured whole route or text resources.
p=args.support_stream
b=p.read_bytes();i=0;supports={};positions=[];road=None
while i+16<=len(b):
 svc,m,n,c,q,pv,iv,k,rc=struct.unpack_from('>HHIHHBBBB',b,i)
 if not 8<=n<=65544 or i+n+8>len(b):raise ValueError('Malformed support stream')
 body=b[i+16:i+n+8];i+=n+8
 if (pv,iv,k,rc)!=(1,1,0,0):continue
 if svc!=0xb006 or len(body)<22:continue
 typ=body[8]
 if m==10 and typ in (29,34) and typ not in supports:
  value=bytearray(body);value[4:8]=struct.pack('>I',a['models'][typ]);value[17:21]=value[4:8];supports[typ]=bytes(value)
 if m==9 and typ==17:positions.append(body)
 if m==14 and typ==40 and road is None:
  assert len(body)==38 and body[13:17]==b'\0\0\0\2' and body[24:32]==b'\0\0\0\x0a\0\0\0\4'
  road=bytearray(body);road[4:8]=struct.pack('>I',a['models'][40]);road[17:21]=road[4:8];road[32:36]=struct.pack('>I',a['resource_id']);road=bytes(road)
assert i==len(b) and set(supports)=={29,34} and road is not None
emptyroad=bytearray(road[:24]+b'\0\0\0\0');emptyroad[9:13]=struct.pack('>I',len(emptyroad)-17);emptyroad=bytes(emptyroad)
position=next(x for x in positions if struct.unpack_from('>d',x,22)[0]>0)
clear=positions[-1];assert struct.unpack_from('>d',clear,22)[0]==0
(root/'support-source.json').write_text(json.dumps({'source':str(p),'models':{k:v.hex() for k,v in supports.items()},'position':position.hex(),'restore_position':clear.hex()},indent=2))
class Trial(SharedDrawingTrial):
 def send(self,m,body):
  if m==11 and struct.unpack_from('>I',body,4)[0]==a['models'][10]:
   super().send(10,supports[34]);super().send(10,supports[29])
  if m==10 and body[8]==15:
   super().send(14,road)
   d=decode_graph_body(m,body)['description'];d.pop('outer_identity_matches');d.pop('model_id');d.pop('model_type')
   d['coming_road_id']=a['models'][40];d['current_state_id']=a['models'][34];d['distance_id']=a['models'][29];d['maneuver_direction']=14
   body=encode_description_body(200,a['models'][15],15,**d)
  super().send(m,body)
  if m==9 and body[8]==33 and decode_graph_body(m,body)['list_state']['guidance_state']==2:super().send(9,position)
 def withdraw(self):
  super().withdraw()
  if self.graph_started:
   row={'method':14,'role':'clear custom road-icon list','acknowledged':False};self.result['cleanup_steps'].append(row)
   try:self.session._empty(14,emptyroad);row['acknowledged']=True
   except Exception as e:row['error']=str(e)
   self.save()
  if self.graph_started:
   row={'method':9,'role':'restore stopped factory destination info','acknowledged':False};self.result['cleanup_steps'].append(row)
   try:self.session._empty(9,clear);row['acknowledged']=True
   except Exception as e:row['error']=str(e)
   self.save()
base=['ssh','-S',str(args.ssh_socket.resolve())];destination='root@'+args.head
with socket.socket() as reserve:
 reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
f='127.0.0.1:%d:160.48.199.96:30502'%port
r=subprocess.run(base+['-O','forward','-L',f,destination],capture_output=True);assert r.returncode==0,r.stderr
report={}
def record(r):
 p=root/'result.tmp';p.write_text(json.dumps(r,indent=2));p.replace(root/'result.json')
def observe(phase,seconds):
 print('TEST WINDOW ACTIVE: %d seconds; keep factory guidance stopped. Ctrl-C withdraws the test.'%args.window_seconds,flush=True)
 time.sleep(args.window_seconds);return None
class BitmapSession(SharedSession):
 def upload_marker(self):
  if custom is None:return super().upload_marker()
  from ric_rle32 import encode_bgra
  a=self.allocation
  self.upload_bitmap(a['resource_id'],a['resource_type'],a['dimensions'],encode_bgra(custom))
def cleanup():signal.signal(signal.SIGINT,signal.SIG_IGN);signal.signal(signal.SIGTERM,signal.SIG_IGN)
def stop(sig,frame):raise KeyboardInterrupt()
signal.signal(signal.SIGTERM,stop)
try:
 with socket.create_connection(('127.0.0.1',port),2) as sock:report=Trial(BitmapSession(TcpExchange(sock,root),a),record,observe,cleanup).run()
finally:
 r=subprocess.run(base+['-O','cancel','-L',f,destination],capture_output=True);report['forward_cancelled']=r.returncode==0
 record(report);print(json.dumps({k:report.get(k) for k in ['status','error','cleanup','cleanup_steps','forward_cancelled']},indent=2))

# A missing cleanup acknowledgement or absence result blocks any next frame.
cleanup_ok=(report.get('status')=='awaiting_visual_verification' and report.get('forward_cancelled') is True and bool(report.get('cleanup_steps')) and all(x.get('acknowledged') is True for x in report['cleanup_steps']) and bool(report.get('cleanup',{}).get('resources')) and all(x.get('dispose_acknowledged') is True and x.get('post_dispose_check') is False for x in report['cleanup']['resources']))
sys.exit(0 if cleanup_ok else 2)
