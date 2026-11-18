"""Real supervisor/worker against the existing loopback server; no new mock classes."""
import json,os,shutil,socket,struct,subprocess,sys,tempfile,time
from pathlib import Path
from standalone_integration import Servers
from resident_startup_deadline import wait
resident,worker,profile,out=map(Path,sys.argv[1:])
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'release';state=Path(tmp)/'ram';root.mkdir(mode=0o700)
 shutil.copy(worker,root/'supra-standalone-parked-qnx');shutil.copy(profile,root/'supra-profile.bin')
 server=Servers('normal',Path(tmp)/'trigger');sentinel=b'factory-owned-image';server.resources[0x01000000]=sentinel;server.start()
 proc=subprocess.Popen([str(resident.resolve()),str(root),str(state),'test-only'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 def command(header,payload=b''):
  with socket.socket(socket.AF_UNIX) as s:
   s.settimeout(4);s.connect(str(state/'factory.sock'));s.sendall(header+payload);return s.recv(64)
 seq=0
 def lane(role,idle):
  global seq
  for method in [9,4]:
   seq+=1;body=struct.pack('>I',100 if role else 200)
   if method==9:
    ident,kind=(101,46) if role else (0x21000000,33)
    payload=struct.pack('>IB',ident,kind)+(struct.pack('>I',0xffffffff if idle else 109) if role else struct.pack('>IIBQQdI',0xffffffff,0xffffffff,0 if idle else 2,0,0,0.,0xffffffff))
    body+=struct.pack('>IBII',ident,kind,len(payload),3 if role else 2)+payload
   p=struct.pack('>HHIHHBBBB',0xb00e if role else 0xb006,method,len(body)+8,1,seq,1,1,0,0)+body
   assert command(b'PRE1'+bytes([role,0,0,0]),struct.pack('>I',len(p))+p)==b'CLEAN\n'
   assert command(b'TESTREQ1',struct.pack('>I',len(p))+p)==b'OK\n'
   ack=p[:4]+struct.pack('>I',8)+p[8:14]+b'\x80\x00';assert command(b'TESTACK1',struct.pack('>I',len(ack))+ack)==b'OK\n'
 try:
  wait(lambda:(state/'ready').exists());lane(0,True);lane(1,True)
  wait(lambda:(state/'worker.starts').exists() and int((state/'worker.starts').read_text())>=3,6)
  assert server.uploads==0 and server.resources=={0x01000000:sentinel}
  assert all(m==2 for m,b in server.requests),server.requests
  evidence=json.loads((root/'fault-first.json').read_text());assert json.loads(evidence['worker.result'])['reason']=='bitmap pool in use'
  assert not (root/'disabled').exists() and proc.poll() is None
  lane(0,False);del server.resources[0x01000000];time.sleep(4.5);assert server.uploads==0
  lane(0,True);wait(lambda:server.uploads>=4,6)
  assert not (root/'disabled').exists();assert command(b'STOPAPP1')==b'CLEAN\n';proc.communicate(timeout=6)
  assert proc.returncode==0 and not server.resources and not server.errors
  assert (root/'fault-first.json').exists()
  out.write_text(json.dumps({'busy_retry_passed':True,'zero_writes_while_busy':True,'factory_image_untouched':True,'active_factory_blocks_retry':True,'returns_after_free_and_idle':True,'cleanup_verified':True,'permanent_reason_saved':True},indent=2));print(out.read_text())
 finally:
  if proc.poll() is None:proc.terminate();proc.wait(timeout=6)
  server.close()
