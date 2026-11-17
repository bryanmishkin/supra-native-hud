"""Loopback reproduction: late clean input exit must not trip startup watchdog."""
import json,os,shutil,socket,struct,subprocess,sys,tempfile,time
from pathlib import Path
from standalone_integration import Servers

def wait(fn,seconds=6):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if fn():return
  time.sleep(.01)
 raise AssertionError('condition deadline')

def run(resident,worker,profile,output):
 results=[]
 for case in ['late-clean-input-exit','never-started']:
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'release';state=Path(tmp)/'state';root.mkdir(mode=0o700)
   shutil.copy(worker,root/'supra-standalone-parked-qnx');shutil.copy(profile,root/'supra-profile.bin')
   server=Servers('normal',Path(tmp)/'trigger');server.start()
   env=os.environ.copy();env['SUPRA_TEST_EXIT_DELAY_US']='300000'
   if case=='never-started':env['SUPRA_TEST_BEFORE_CONTROL_US']='4000000'
   proc=subprocess.Popen([str(resident.resolve()),str(root),str(state),'test-only'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
   def command(header,payload=b''):
    with socket.socket(socket.AF_UNIX) as s:
     s.settimeout(4);s.connect(str(state/'factory.sock'));s.sendall(header+payload);return s.recv(64)
   seq=0
   try:
    wait(lambda:(state/'ready').exists())
    for role in [0,1]:
     for method in [9,4]:
      seq+=1;body=struct.pack('>I',100 if role else 200)
      if method==9:
       ident,kind=(101,46) if role else (0x21000000,33)
       payload=struct.pack('>IB',ident,kind)+(struct.pack('>I',0xffffffff) if role else struct.pack('>IIBQQdI',0xffffffff,0xffffffff,0,0,0,0.,0xffffffff))
       body+=struct.pack('>IBII',ident,kind,len(payload),3 if role else 2)+payload
      packet=struct.pack('>HHIHHBBBB',0xb00e if role else 0xb006,method,len(body)+8,1,seq,1,1,0,0)+body
      assert command(b'PRE1'+bytes([role,0,0,0]),struct.pack('>I',len(packet))+packet)==b'CLEAN\n'
      assert command(b'TESTREQ1',struct.pack('>I',len(packet))+packet)==b'OK\n'
      ack=packet[:4]+struct.pack('>I',8)+packet[8:14]+b'\x80\x00'
      assert command(b'TESTACK1',struct.pack('>I',len(ack))+ack)==b'OK\n'
    if case=='late-clean-input-exit':
     wait(lambda:server.uploads>=3);time.sleep(3.2);server.mode='rpm-timeout'
     wait(lambda:(state/'last-result').exists())
     result=json.loads((state/'last-result').read_text());assert result['cleanup_verified'] and result['frames']>=3
     time.sleep(.4)
     assert proc.poll() is None and not (root/'disabled').exists(), 'late clean input exit incorrectly quarantined: '+(state/'resident.status').read_text()
     server.mode='normal';before=server.uploads;wait(lambda:server.uploads>before+2)
     assert command(b'STOPAPP1')==b'CLEAN\n';proc.communicate(timeout=5);assert proc.returncode==0
    else:
     proc.communicate(timeout=8);assert proc.returncode==2
     assert (root/'disabled').read_text()=='worker startup deadline\n'
    assert not server.resources and not server.errors
    results.append({'case':case,'passed':True})
   finally:
    if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
    server.close()
 output.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
if __name__=='__main__':run(*map(Path,sys.argv[1:]))
