"""Real resident + real native worker; local fake cluster/RPM only."""
import sys,tempfile,socket,struct,time,subprocess,json,shutil,os
from pathlib import Path
from standalone_integration import Servers,exact
resident,worker,profile,out=map(Path,sys.argv[1:])
def wait(fn,limit=4):
 end=time.monotonic()+limit
 while time.monotonic()<end:
  if fn():return
  time.sleep(.01)
 raise AssertionError('condition deadline')
def packet(role,method,seq,idle):
 b=struct.pack('>I',100 if role else 200)
 if method==9:
  ident,kind=(101,46) if role else (0x21000000,33)
  payload=struct.pack('>IB',ident,kind)
  payload+=struct.pack('>I',0xffffffff if idle else 109) if role else struct.pack('>IIBQQdI',0xffffffff,0xffffffff,0 if idle else 2,0,0,0.,0xffffffff)
  b+=struct.pack('>IBII',ident,kind,len(payload),3 if role else 2)+payload
 return struct.pack('>HHIHHBBBB',0xb00e if role else 0xb006,method,len(b)+8,1,seq,1,1,0,0)+b
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'release';state=Path(tmp)/'state';root.mkdir(mode=0o700)
 shutil.copy(worker,root/'supra-standalone-parked-qnx');shutil.copy(profile,root/'supra-profile.bin')
 server=Servers('normal',Path(tmp)/'trigger');server.start();env=os.environ.copy();env['SUPRA_TEST_EXIT_DELAY_US']='150000';proc=subprocess.Popen([str(resident.resolve()),str(root),str(state),'test-only'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
 def command(header,payload=b''):
  with socket.socket(socket.AF_UNIX) as s:
   s.settimeout(4);s.connect(str(state/'factory.sock'));s.sendall(header+payload);return s.recv(64)
 seq=0
 def event(role,method,idle):
  global seq
  seq+=1;p=packet(role,method,seq,idle)
  assert command(b'PRE1'+bytes([role,0,0,0]),struct.pack('>I',len(p))+p)==b'CLEAN\n'
  # Pre-send acceptance must come AFTER worker resources have been removed.
  assert not server.resources,server.resources
  assert command(b'TESTREQ1',struct.pack('>I',len(p))+p)==b'OK\n'
  ack=p[:4]+struct.pack('>I',8)+p[8:14]+b'\x80\x00'
  assert command(b'TESTACK1',struct.pack('>I',len(ack))+ack)==b'OK\n'
 def state_event(role,idle):event(role,9,idle);event(role,4,idle)
 try:
  wait(lambda:(state/'ready').exists());time.sleep(.1);assert not server.uploads
  state_event(0,True);assert not server.uploads
  state_event(1,True);wait(lambda:server.uploads>=4);time.sleep(3.2)
  state_event(0,False);wait(lambda:not server.resources);before=server.uploads;time.sleep(.15);assert server.uploads==before
  state_event(0,True);wait(lambda:server.uploads>before+2)
  state_event(1,False);wait(lambda:not server.resources);before=server.uploads;time.sleep(.15);assert server.uploads==before
  state_event(1,True);wait(lambda:server.uploads>before+2)
  assert command(b'STOPAPP1')==b'CLEAN\n';stdout,stderr=proc.communicate(timeout=5)
  assert proc.returncode==0,(stdout,stderr,(state/'resident.status').read_text())
  assert not server.resources and not (state/'factory.sock').exists()
  result={'navigation_stop_and_return':True,'radio_stop_and_return':True,'cleanup_before_factory_send':True,'boot_unknown_standby':True,'manual_stop_clean':True,'worker_starts':int((state/'worker.starts').read_text()),'factory_requests':seq,'errors':server.errors}
  assert not server.errors;out.write_text(json.dumps(result,indent=2));print(out.read_text())
 finally:
  if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
  server.close()
# An acknowledged transport failure must quarantine rather than spin/reclaim.
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'release';state=Path(tmp)/'state';root.mkdir(mode=0o700)
 shutil.copy(worker,root/'supra-standalone-parked-qnx');shutil.copy(profile,root/'supra-profile.bin')
 server=Servers('lost-ack',Path(tmp)/'trigger');server.start();proc=subprocess.Popen([str(resident.resolve()),str(root),str(state),'test-only'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  wait(lambda:(state/'ready').exists());state_event(0,True);state_event(1,True)
  stdout,stderr=proc.communicate(timeout=6)
  assert proc.returncode==2 and (root/'disabled').exists(),(stdout,stderr)
  assert 'QUARANTINED' in (state/'resident.status').read_text()
  result['transport_failure_quarantines']=True;out.write_text(json.dumps(result,indent=2))
 finally:
  if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
  server.close()
print('Uncertain cleanup quarantines without automatic retry')

# Clean RPM timeout may retry, but uncertain drawing transport above may not.
for recovery in [True,False]:
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp)/'release';state=Path(tmp)/'state';root.mkdir(mode=0o700)
  shutil.copy(worker,root/'supra-standalone-parked-qnx');shutil.copy(profile,root/'supra-profile.bin')
  server=Servers('rpm-timeout',Path(tmp)/'trigger');server.start();proc=subprocess.Popen([str(resident.resolve()),str(root),str(state),'test-only'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  try:
   wait(lambda:(state/'ready').exists());state_event(0,True);state_event(1,True)
   wait(lambda:(state/'last-result').exists());assert not server.resources
   assert json.loads((state/'last-result').read_text())['cleanup_verified']
   if recovery:
    server.mode='normal';before=server.uploads;wait(lambda:server.uploads>before+2,5)
    assert command(b'STOPAPP1')==b'CLEAN\n';proc.communicate(timeout=5);assert proc.returncode==0;assert not server.resources
   else:
    proc.communicate(timeout=13);assert proc.returncode==2;assert int((state/'worker.starts').read_text())==4;assert not server.resources
    assert 'retry budget exhausted' in (state/'resident.status').read_text()
  finally:
   if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
   server.close()
print('Clean RPM timeout recovery and bounded retry exhaustion passed')

# A factory event may arrive after fork but before the child can draw or listen.
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'release';state=Path(tmp)/'state';root.mkdir(mode=0o700)
 shutil.copy(worker,root/'supra-standalone-parked-qnx');shutil.copy(profile,root/'supra-profile.bin')
 server=Servers('normal',Path(tmp)/'trigger');server.start();env=os.environ.copy();env['SUPRA_TEST_BEFORE_CONTROL_US']='400000'
 proc=subprocess.Popen([str(resident.resolve()),str(root),str(state),'test-only'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
 try:
  wait(lambda:(state/'ready').exists());state_event(0,True);state_event(1,True);wait(lambda:(state/'worker.starts').exists())
  state_event(0,False);time.sleep(.6);assert not server.uploads;assert proc.poll() is None
  state_event(0,True);wait(lambda:server.uploads>=3,5);assert command(b'STOPAPP1')==b'CLEAN\n';proc.communicate(timeout=5);assert proc.returncode==0;assert not server.resources
 finally:
  if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
  server.close()
print('Pre-admission factory takeover blocks all drawing and resumes cleanly')
