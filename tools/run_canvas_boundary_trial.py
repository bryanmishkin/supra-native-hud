#!/usr/bin/env python3
import sys,socket,subprocess,json,time,signal,struct,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ric_shared_trial import SharedSession,SharedDrawingTrial,allocation_from_reply
from ric_live_trial import TcpExchange
from ric_graph import decode_graph_body,encode_description_body
parser=argparse.ArgumentParser(description='Experimental, parked B006 bitmap-size boundary test. NOT the installed V1 worker.')
parser.add_argument('--execute',action='store_true')
parser.add_argument('--double-buffer',action='store_true',help='Experimental two-slot switch, no deliberate blank between frames')
parser.add_argument('--live-rpm-local',help='Explicit parked measured-RPM experiment')
parser.add_argument('--live-seconds',type=int,choices=[10,30],default=10)
parser.add_argument('--swap-red-blue',action='store_true',help='Measured Supra road-icon color correction, applied once before RLE encoding')
parser.add_argument('--renderer-style',choices=['classic','sport'],default='classic')
parser.add_argument('--renderer',type=Path,help='Locally built native bitmap renderer')
parser.add_argument('--graph-variant',choices=['control','no-detail','road-only','empty-detail','empty-direction-zero'],default='control',help='Control and empty-direction-zero live verified on this Supra; other variants experimental')
parser.add_argument('--bitmap-bgra',type=Path,help='Optional 150x36 opaque BGRA test frame')
parser.add_argument('--guidance-stopped',action='store_true',help='Operator confirmed guidance and selector stopped')
parser.add_argument('--window-seconds',type=int,choices=range(1,16),default=15)
parser.add_argument('--create-response',type=Path)
parser.add_argument('--support-stream',type=Path)
parser.add_argument('--ssh-socket',type=Path)
parser.add_argument('--head')
parser.add_argument('--output',type=Path)
parser.add_argument('--canvas-dim',required=True,choices=['150x48','150x72','150x144'],help='Explicit candidate dimensions larger than the negotiated 150x36 bitmap. Test one size per run.')
parser.add_argument('--v1-stopped-clean',action='store_true',help='Acknowledge the separately confirmed boot-local CLEAN stop of the resident; tool also verifies STOPPED state remotely.')
args=parser.parse_args()
if args.execute and (not args.v1_stopped_clean or not args.guidance_stopped or args.double_buffer or args.live_rpm_local or args.renderer or args.bitmap_bgra or args.graph_variant != 'control'):
    parser.error('Canvas boundary test requires --v1-stopped-clean --guidance-stopped and forbids RPM/renderer/bitmap/experimental-graph/double-buffer options')

if not args.execute:
 print('Offline plan only: compare a known-good 150x36 B006 graph with one alternate bitmap size ('+args.canvas_dim+'). Requires separately verified boot-local V1 CLEAN stop, free bitmap pool, and factory guidance idle. This is NOT a PiP upload or a full-canvas claim.');sys.exit(0)
if not all((args.create_response,args.support_stream,args.ssh_socket,args.head,args.output)):parser.error('All file/connection/output arguments required')
if (args.live_rpm_local or args.bitmap_bgra or args.graph_variant!='control') and not args.guidance_stopped:parser.error('Custom frames require --guidance-stopped')
from ric_rle32 import swap_red_blue
def display_pixels(raw):return swap_red_blue(raw) if args.swap_red_blue else raw
custom = args.bitmap_bgra.read_bytes() if args.bitmap_bgra else None
if custom is not None and (len(custom)!=150*36*4 or any(x!=255 for x in custom[3::4])):parser.error('Expected exactly 150x36 opaque BGRA')
if args.live_rpm_local and args.graph_variant in ('empty-detail','empty-direction-zero') and not args.double_buffer:parser.error('Empty-detail live test requires two-slot updates')
if args.double_buffer and not args.live_rpm_local:parser.error('Double buffer requires live RPM')
if args.live_rpm_local and (not args.renderer or args.bitmap_bgra or args.graph_variant not in ('control','empty-detail','empty-direction-zero')):parser.error('Live RPM requires renderer, supported graph and no static bitmap')
import ipaddress
ipaddress.IPv4Address(args.head)
if args.live_rpm_local and not ipaddress.IPv4Address(args.live_rpm_local).is_link_local:parser.error('Expected local ENET address')
root=args.output;root.mkdir(parents=True,exist_ok=False)
a=allocation_from_reply(args.create_response.read_bytes()[16:])
# Preserve the saved, vehicle-verified create configuration for allocation;
# override only dimensions of the test upload, NEVER the saved create response.
a['dimensions']=[int(v) for v in args.canvas_dim.split('x')]
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
   if args.graph_variant in ('empty-detail','empty-direction-zero'):
    from ric_guiding import encode_empty_guiding_body
    super().send(11,encode_empty_guiding_body(200,a['models'][10],10));return
   if args.graph_variant!='control':return
  if m==10 and body[8]==15:
   super().send(14,road)
   d=decode_graph_body(m,body)['description'];d.pop('outer_identity_matches');d.pop('model_id');d.pop('model_type')
   d['coming_road_id']=a['models'][40];d['current_state_id']=a['models'][34];d['distance_id']=a['models'][29];d['maneuver_direction']=14
   if args.graph_variant in ('no-detail','road-only'):d['detailed_maneuver_id']=0xffffffff
   if args.graph_variant in ('road-only','empty-detail'):d['maneuver_direction']=8
   if args.graph_variant=='empty-direction-zero':d['maneuver_direction']=0
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
# This is a deliberately strict gate. STOPAPP1 is boot-local and cooperative;
# it does not write the release's persistent disabled marker or replace V1.
# Do not auto-stop the app here: that is an explicit separate owner action.
preflight_command=(
    'test ! -S /tmp/supra-hud-v1/factory.sock && '
    'grep -qx STOPPED /tmp/supra-hud-v1/resident.status && '
    'grep -qx cleanup_proven=true /var/opt/supra-hud/v1/last-resident.status && '
    'test ! -e /var/opt/supra-hud/v1/disabled && '
    '! pidin ar | grep supra-standalone-parked-qnx >/dev/null'
)
try:
    checked=subprocess.run(base+[destination,preflight_command],capture_output=True,timeout=10)
except subprocess.TimeoutExpired:
    parser.error('V1 CLEAN-stop verification timed out. Refusing to connect to the cluster.')
if checked.returncode != 0:
    parser.error('V1 boot-local CLEAN-stop checks did not all pass. No test drawing sent. Remote stderr: '+checked.stderr.decode('utf-8','replace')[:200])
with socket.socket() as reserve:
 reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
f='127.0.0.1:%d:160.48.199.96:30502'%port
r=subprocess.run(base+['-O','forward','-L',f,destination],capture_output=True);assert r.returncode==0,r.stderr
report={}
def record(r):
 r['canvas_boundary_test']={'candidate_dimensions':a['dimensions'],'known_verified_dimensions':[150,36],
                            'pi_p_test':False,'full_canvas_proven':False,
                            'interpretation':'Protocol acceptance plus owner-confirmed windshield pixels only; failed acceptance does not rule out other display routes.'}
 r['renderer_style']=args.renderer_style;r['swap_red_blue']=args.swap_red_blue
 r['live_rpm']=bool(args.live_rpm_local);r['double_buffer']=args.double_buffer;r['graph_variant']=args.graph_variant
 p=root/'result.tmp';p.write_text(json.dumps(r,indent=2));p.replace(root/'result.json')
def observe(phase,seconds):
 if args.live_rpm_local:return live_updates()
 print('TEST WINDOW ACTIVE: %d seconds; keep factory guidance stopped. Ctrl-C withdraws the test.'%args.window_seconds,flush=True)
 import select
 if sys.stdin.isatty():
  print('Did the complete taller frame show on the WINDSHIELD? Type y or n then Return before the window ends; no response = unknown.',flush=True)
  ready,_,_=select.select([sys.stdin],[],[],args.window_seconds)
  if ready:
   answer=sys.stdin.readline().strip().lower()
   if answer in ('y','yes'):return True
   if answer in ('n','no'):return False
  return None
 time.sleep(args.window_seconds);return None
class BitmapSession(SharedSession):
 def upload_bitmap(self,rid,typ,pair,image):
  # Defer error cleanup until the graph has been withdrawn; another slot may
  # still be visible when this upload fails or its acknowledgement is lost.
  from ric_resource import encode_bitmap_body
  self._active()
  if rid in self.resources or self._check(rid,typ):raise RuntimeError('Bitmap slot not free')
  self.resources[rid]=typ
  self._empty(3,encode_bitmap_body(self.handle,rid,typ,pair,image))
  if not self._check(rid,typ):raise RuntimeError('Uploaded bitmap not present')
 def upload_marker(self):
  # Same already-proven V1 pixel image/graph; only uploaded width/height differ.
  from ric_rle32 import marker_bgra,encode_bgra
  dimensions=self.allocation['dimensions'];raw=marker_bgra(*dimensions)
  self.upload_bitmap(self.allocation['resource_id'],self.allocation['resource_type'],dimensions,encode_bgra(display_pixels(raw)))
  return
  if args.live_rpm_local:
   raw=measured_frame();a=self.allocation
   from ric_rle32 import encode_bgra
   self.upload_bitmap(a['resource_id'],a['resource_type'],a['dimensions'],encode_bgra(raw));return
  if custom is None:return super().upload_marker()
  from ric_rle32 import encode_bgra
  a=self.allocation
  self.upload_bitmap(a['resource_id'],a['resource_type'],a['dimensions'],encode_bgra(display_pixels(custom)))
latest_sample=None
live_session=None
live_rows=[]
stop_reason='duration_complete'
from request_navigation_yield import check_yield,NavigationYield,handoff_ready
def fresh():
 check_yield(root)
 if latest_sample is None or time.monotonic()*1000-latest_sample['sampled_at_ms']>300:raise RuntimeError('RPM sample expired; withdrawing')
def measured_frame():
 global latest_sample
 from rpm_feed import sample
 latest_sample=sample(args.live_rpm_local,'169.254.106.96','en8',timeout=.1)
 live_rows.append(latest_sample)
 (root/'live-rpm.json').write_text(json.dumps(live_rows,indent=2))
 if not latest_sample['valid']:raise RuntimeError('RPM invalid; withdrawing')
 target=root/'current.bgra'
 subprocess.run([str(args.renderer.resolve()),str(latest_sample['rpm']),str(target)]+(['sport'] if args.renderer_style=='sport' else []),check=True,capture_output=True,timeout=.1)
 raw=target.read_bytes()
 if len(raw)!=21600:raise ValueError('Bad native frame')
 fresh();return display_pixels(raw)
def live_updates():
 from ric_guiding import encode_high_roundabout_body
 from ric_rle32 import encode_bgra
 from ric_resource import encode_bitmap_body
 global stop_reason
 session=live_session;rid=a['resource_id'];typ=a['resource_type']
 print('LIVE RPM WINDOW ACTIVE: %d seconds; idle only'%args.live_seconds,flush=True)
 deadline=time.monotonic()+args.live_seconds
 # Tight per-request timeout while displaying; cleanup restores normal timeout.
 session.timeout=.1
 try:
  fresh()
  while time.monotonic()<deadline:
   if args.double_buffer:
    new_id=next(x for x in session.upload_ids if x!=rid)
    raw=measured_frame()
    session.upload_bitmap(new_id,typ,a['dimensions'],encode_bgra(raw));fresh()
    nextroad=bytearray(road);nextroad[32:36]=struct.pack('>I',new_id)
    if args.graph_variant not in ('empty-detail','empty-direction-zero'):session._empty(11,encode_high_roundabout_body(200,a['models'][10],10,0,2,new_id))
    fresh()
    session._empty(14,bytes(nextroad));fresh()
    session._empty(8,struct.pack('>II',200,rid))
    if session._check(rid,typ):raise RuntimeError('Previous bitmap still present')
    del session.resources[rid];rid=new_id
   else:
    session._empty(14,emptyroad)
    session._empty(11,encode_high_roundabout_body(200,a['models'][10],10,0,2,0xffffffff))
    session._empty(8,struct.pack('>II',200,rid))
    if session._check(rid,typ):raise RuntimeError('Old bitmap still present')
    del session.resources[rid]
    raw=measured_frame()
    session.upload_bitmap(rid,typ,a['dimensions'],encode_bgra(raw));fresh()
    if args.graph_variant not in ('empty-detail','empty-direction-zero'):session._empty(11,encode_high_roundabout_body(200,a['models'][10],10,0,2,rid))
    fresh();session._empty(14,road);fresh()
   # Keep polling at <=4Hz. Remove references before acquiring the next sample.
   remaining=.25-(time.monotonic()*1000-latest_sample['sampled_at_ms'])/1000
   if remaining>0:time.sleep(min(remaining,max(0,deadline-time.monotonic())))
  return None
 except NavigationYield:
  stop_reason='factory_navigation_request';return None
 finally:session.timeout=2

def cleanup():signal.signal(signal.SIGINT,signal.SIG_IGN);signal.signal(signal.SIGTERM,signal.SIG_IGN)
def stop(sig,frame):raise KeyboardInterrupt()
signal.signal(signal.SIGTERM,stop)
try:
 with socket.create_connection(('127.0.0.1',port),2) as sock:
  live_session=BitmapSession(TcpExchange(sock,root),a,double_buffer=args.double_buffer)
  report=Trial(live_session,record,observe,cleanup).run()
finally:
 r=subprocess.run(base+['-O','cancel','-L',f,destination],capture_output=True);report['forward_cancelled']=r.returncode==0
 report['stop_reason']=stop_reason
 (root/'navigation-handoff.json').write_text(json.dumps(dict(protocol_ready=handoff_ready(report),visual_confirmation_required=True,automatic_resume=False),indent=2)+'\n')
 record(report);print(json.dumps({k:report.get(k) for k in ['status','error','cleanup','cleanup_steps','forward_cancelled']},indent=2))

# A missing cleanup acknowledgement or absence result blocks any next frame.
cleanup_ok=(report.get('status')=='awaiting_visual_verification' and report.get('forward_cancelled') is True and bool(report.get('cleanup_steps')) and all(x.get('acknowledged') is True for x in report['cleanup_steps']) and bool(report.get('cleanup',{}).get('resources')) and all(x.get('dispose_acknowledged') is True and x.get('post_dispose_check') is False for x in report['cleanup']['resources']))
# Exit zero only asserts protocol/cleanup. The result JSON's owner visual field
# independently determines whether larger pixels actually appeared.
report['canvas_boundary_test']['protocol_and_cleanup_pass']=cleanup_ok
record(report)
sys.exit(0 if cleanup_ok else 2)
