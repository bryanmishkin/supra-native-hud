"""Replay private captured movement requests through the real resident/worker.
Loopback only. Does not contact a vehicle or include factory captures in Git.
"""
import ctypes,json,os,shutil,socket,struct,subprocess,sys,tempfile,time
from pathlib import Path
from standalone_integration import Servers
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from extract_someip_pcap import extract
resident,worker,profile,bridge,pcap,failed_req,failed_reply,out=map(Path,sys.argv[1:])
lib=ctypes.CDLL(str(bridge.resolve()));lib.supra_background.argtypes=[ctypes.c_void_p,ctypes.c_uint];lib.supra_background.restype=ctypes.c_int
captured=[]
for flow in extract(pcap.read_bytes(),max_packets=65536)['streams']:
 if flow['flow'][2:]!=['160.48.199.96',30502]:continue
 raw=flow['data'];offset=0
 while offset+16<=len(raw):
  n=struct.unpack_from('>I',raw,offset+4)[0]+8
  if n<16 or offset+n>len(raw):break
  packet=raw[offset:offset+n];offset+=n
  if lib.supra_background(packet,len(packet)):captured.append(packet)
assert len(captured)>=60,len(captured)
def wait(fn,limit=5):
 end=time.monotonic()+limit
 while time.monotonic()<end:
  if fn():return
  time.sleep(.01)
 raise AssertionError('condition deadline')
def model(role,seq,idle):
 ident,kind=(101,46) if role else (0x21000000,33)
 payload=struct.pack('>IB',ident,kind)+(struct.pack('>I',0xffffffff if idle else 109) if role else struct.pack('>IIBQQdI',0xffffffff,0xffffffff,0 if idle else 2,0,0,0.,0xffffffff))
 body=struct.pack('>IIBII',100 if role else 200,ident,kind,len(payload),3 if role else 2)+payload
 return struct.pack('>HHIHHBBBB',0xb00e if role else 0xb006,9,len(body)+8,1,seq,1,1,0,0)+body
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'release';state=Path(tmp)/'state';root.mkdir(mode=0o700);shutil.copy(worker,root/'supra-standalone-parked-qnx');shutil.copy(profile,root/'supra-profile.bin')
 server=Servers('normal',Path(tmp)/'trigger');server.start();proc=subprocess.Popen([str(resident.resolve()),str(root),str(state),'test-only'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 def cmd(h,p=b''):
  with socket.socket(socket.AF_UNIX) as s:s.settimeout(4);s.connect(str(state/'factory.sock'));s.sendall(h+p);return s.recv(64)
 def event(p,reply=None):
  assert cmd(b'PRE1'+bytes([p[1]==14,0,0,0]),struct.pack('>I',len(p))+p)==b'CLEAN\n'
  assert cmd(b'TESTREQ1',struct.pack('>I',len(p))+p)==b'OK\n'
  if reply is None:reply=p[:4]+struct.pack('>I',8)+p[8:14]+b'\x80\x00'
  assert cmd(b'TESTACK1',struct.pack('>I',len(reply))+reply)==b'OK\n'
 def state_event(role,seq,idle):
  event(model(role,seq,idle));body=struct.pack('>I',100 if role else 200);event(struct.pack('>HHIHHBBBB',0xb00e if role else 0xb006,4,12,1,seq+1,1,1,0,0)+body)
 try:
  wait(lambda:(state/'ready').exists());state_event(0,40000,True);state_event(1,40010,True);wait(lambda:server.uploads>=3);starts=(state/'worker.starts').read_text();uploads=server.uploads
  for p in captured:
   event(p);assert (state/'worker.starts').read_text()==starts;assert not (root/'disabled').exists()
  event(failed_req.read_bytes(),failed_reply.read_bytes());wait(lambda:server.uploads>uploads+3)
  assert (state/'worker.starts').read_text()==starts and not (root/'disabled').exists() and not (state/'last-result').exists()
  assert not any(m==9 and len(b)==59 and b[30] in (0,5) for m,b in server.requests)
  # Real visibility takeover must still remove the tach before factory sending.
  state_event(0,41000,False);assert not server.resources
  old=server.uploads;state_event(0,41010,True);wait(lambda:server.uploads>old+2)
  # An error deleting a bitmap remains a fault, even with otherwise identical reply.
  bad=bytearray(failed_req.read_bytes());bad[-4:]=bytes.fromhex('01000008');bad[10:12]=struct.pack('>H',42000);bad=bytes(bad)
  assert cmd(b'PRE1'+bytes(4),struct.pack('>I',len(bad))+bad)==b'CLEAN\n';assert not server.resources
  assert cmd(b'TESTREQ1',struct.pack('>I',len(bad))+bad)==b'OK\n';reply=bad[:4]+struct.pack('>I',8)+bad[8:14]+b'\x81\x01'
  assert cmd(b'TESTACK1',struct.pack('>I',len(reply))+reply)==b'ERROR\n';proc.communicate(timeout=5);assert proc.returncode==2;assert (root/'disabled').read_text()=='factory request failed\n'
  assert not server.errors,server.errors
  report={'captured_background_requests':len(captured),'captured_text_removal_error_tolerated_without_restart':True,'background_replay_worker_starts':int(starts),'visibility_takeover_cleanup_and_return':True,'bitmap_removal_error_still_quarantines':True,'vehicle_connections':0}
  out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
 finally:
  if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
  server.close()
