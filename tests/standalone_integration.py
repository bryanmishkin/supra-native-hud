#!/usr/bin/env python3
"""Explicit loopback-only native integration/fault tests; never contacts a car."""
import socket,struct,threading,subprocess,tempfile,json,sys,time,os,signal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_resource import decode_resource_body
from ric_rle32 import decode_bgra

def exact(s,n):
 b=b''
 while len(b)<n:
  x=s.recv(n-len(b))
  if not x:raise EOFError()
  b+=x
 return b
class Servers:
 def __init__(self,mode,trigger):
  self.mode=mode;self.trigger=trigger;self.resources={};self.requests=[];self.images=[];self.stop=False;self.errors=[];self.ready=threading.Event();self.sockets=[];self.threads=[];self.uploads=0;self.sequences=[]
 def start(self):
  for port,fn in ((30502,self.ric),(6801,self.rpm)):
   s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port));s.listen();s.settimeout(.1);self.sockets.append(s)
   t=threading.Thread(target=self.serve,args=(s,fn),daemon=True);t.start();self.threads.append(t)
 def serve(self,s,fn):
  while not self.stop:
   try:c,_=s.accept()
   except socket.timeout:continue
   except OSError:break
   try:
    c.settimeout(3)
    with c:fn(c)
   except (EOFError,ConnectionError,OSError):pass
   except Exception as e:self.errors.append(repr(e))
 def ric(self,c):
  while not self.stop:
   h=exact(c,16);svc,m,n,client,seq,pv,iv,k,rc=struct.unpack('>HHIHHBBBB',h);b=exact(c,n-8);self.requests.append((m,b));self.sequences.append(seq);assert (svc,client,pv,iv,k,rc)==(0xb006,0x5348,1,1,0,0);assert m not in (1,7)
   result=b''
   if m==2:
    rid=struct.unpack_from('>I',b,4)[0];result=bytes([rid in self.resources or (self.mode=='busy' and rid==0x01000000)])
   if m==3:
    d=decode_resource_body(b);rid=d['resource_id'];assert rid not in self.resources;raw=decode_bgra(b[30:],5400);self.images.append(raw);self.resources[rid]=raw;self.uploads+=1
    if self.mode=='lost-ack' and self.uploads==2:return
   if m==8 and self.mode=='lost-remove-ack':return
   if m==8:
    rid=struct.unpack_from('>I',b,4)[0];assert rid in self.resources;del self.resources[rid]
   if self.mode in ('factory','monitor-loss') and self.uploads==2 and m==2:self.trigger.touch()
   reply=struct.pack('>HHIHHBBBB',svc,m,len(result)+8,client,seq,1,1,128,0)+result
   # Exercise stream fragmentation and both idle-cookie handling and correlation.
   if self.mode=='bad-reply' and self.uploads==2:reply=reply[:10]+struct.pack('>H',seq+1)+reply[12:]
   if len(self.requests)==1:c.sendall(bytes.fromhex('ffff800000000008deadbeef01010200'))
   for part in (reply[:7],reply[7:]):c.sendall(part)
 def rpm(self,c):
  q=exact(c,10);assert q==bytes.fromhex('000000040001f412010c')
  if self.mode=='rpm-timeout' and self.uploads:time.sleep(.35);return
  c.sendall(bytes.fromhex('00000006000112f4410c6590')) # 6500 RPM
 def close(self):
  self.stop=True
  for s in self.sockets:s.close()
  for t in self.threads:t.join(4)
def run(exe,profile,out):
 out.mkdir(parents=True,exist_ok=False);summary=[]
 for mode in ('normal','signal','busy','factory','lost-ack','bad-reply','rpm-timeout','monitor-loss','cooperative-yield','continuous-stop','sequence-wrap'):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);trigger=root/'factory';server=Servers(mode,trigger);server.start();env=os.environ.copy();env['SUPRA_TEST_MONITOR_LOSS' if mode=='monitor-loss' else 'SUPRA_TEST_FACTORY_TRIGGER']=str(trigger)
   if mode=='sequence-wrap':env['SUPRA_TEST_SEQUENCE_START']='65530'
   try:
    proc=subprocess.Popen([str(exe.resolve()),'--continuous-parked-guidance-stopped' if mode=='continuous-stop' else '--parked-guidance-stopped',str(profile.resolve()),'127.0.0.1','127.0.0.1','127.0.0.1','test-only','0' if mode=='continuous-stop' else '1',str(root/'journal')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,text=True)
    if mode in ('signal','cooperative-yield','continuous-stop'):
     for _ in range(200):
      if server.uploads>=2:break
      time.sleep(.005)
     if mode in ('signal','continuous-stop'):
      if mode=='continuous-stop':
       time.sleep(1.3);assert proc.poll() is None
      proc.send_signal(signal.SIGTERM)
     else:
      with socket.socket(socket.AF_UNIX) as control:
       control.settimeout(3);control.connect(str(root/'journal')+'.handoff');control.sendall(b'YIELD1\n');assert exact(control,6)==b'CLEAN\n'
    stdout,stderr=proc.communicate(timeout=8);report=json.loads(stdout);assert not server.errors,server.errors
    if mode in ('normal','signal','cooperative-yield','continuous-stop','sequence-wrap'):assert proc.returncode==0 and report['cleanup_verified'] and not server.resources
    elif mode=='busy':assert proc.returncode==2 and server.uploads==0
    elif mode=='rpm-timeout':assert proc.returncode==2 and report['cleanup_verified'] and not server.resources
    else:
     assert proc.returncode==2 and not report['cleanup_verified']
     # On factory/uncertain transport, don't issue cancel/idle or delete images.
     assert not any(m==8 for m,b in server.requests)
     assert not any(m==9 and len(b)==59 and b[30] in (0,5) for m,b in server.requests)
    if mode=='sequence-wrap':assert 65535 in server.sequences and 1 in server.sequences
    if mode=='factory':assert report['factory_activity']
    if mode=='monitor-loss':assert report['monitor_unknown']
    if server.images:
     # Red correction is applied once: target input B=255 G=40 R=0.
     assert bytes((255,40,0,255)) in server.images[0]
    report.update(case=mode,exit_code=proc.returncode,request_count=len(server.requests));summary.append(report)
    (out/(mode+'.json')).write_text(json.dumps(report,indent=2));(out/(mode+'-journal.jsonl')).write_text((root/'journal').read_text())
   finally:server.close()
 (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
