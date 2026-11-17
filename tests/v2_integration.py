#!/usr/bin/env python3
"""Loopback-only V2 worker/pressure integration; never connects to a vehicle."""
import json,struct,subprocess,sys,tempfile,time,socket
from pathlib import Path
from standalone_integration import Servers,exact
class V2Servers(Servers):
 def __init__(self,mode,trigger):
  super().__init__('normal',trigger);self.boost_mode=mode;self.pressures=0;self.rpms=0
 def rpm(self,c):
  h=exact(c,6);n,kind=struct.unpack('>IH',h);q=exact(c,n)
  assert kind==1 and q[:2]==b'\xf4\x12'
  if q[2:]==b'\x01\x0c':
   self.rpms+=1;c.sendall(bytes.fromhex('00000006000112f4410c0a28'));return
  assert q[2:] in (b'\x22\x42\x05',b'\x22\x42\x01');self.pressures+=1
  if self.boost_mode=='timeout':time.sleep(.12);return
  if self.boost_mode=='unavailable':body=b'\x12\xf4\x7f\x22\x31'
  else:
   did=q[-2:];raw=b'\x31\xec' if did==b'\x42\x05' else b'\x63\xd3'
   if self.boost_mode=='wrong-did':did=b'\x42\x02'
   if self.boost_mode=='sentinel':raw=b'\xff\xff'
   body=b'\x12\xf4\x62'+did+raw
  c.sendall(struct.pack('>IH',len(body),1)+body)
def run(exe,profile,out):
 out.mkdir(parents=True,exist_ok=False);results=[]
 for mode in ['rpm-only','paired','unavailable','timeout','wrong-did','sentinel','yield']:
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);server=V2Servers(mode,root/'trigger');server.start()
   try:
    option='--parked-v2-guidance-stopped' if mode=='rpm-only' else '--parked-v2-boost-candidate'
    cmd=[str(exe.resolve()),option,str(profile.resolve()),'127.0.0.1','127.0.0.1','127.0.0.1','test-only','2',str(root/'journal')]
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if mode=='yield':
     for _ in range(200):
      if server.uploads>=2:break
      time.sleep(.005)
     with socket.socket(socket.AF_UNIX) as control:
      control.settimeout(3);control.connect(str(root/'journal')+'.handoff');control.sendall(b'YIELD1\n');assert exact(control,6)==b'CLEAN\n'
    stdout,stderr=proc.communicate(timeout=8)
    p=subprocess.CompletedProcess(cmd,proc.returncode,stdout,stderr)
    report=json.loads(p.stdout);assert p.returncode==0,(mode,report,p.stderr)
    assert report['cleanup_verified'] and not server.resources and not server.errors
    assert report['frames']>=(2 if mode=='yield' else 4) and server.rpms>=(2 if mode=='yield' else 4)
    if mode=='yield':assert report['reason']=='factory_navigation_request'
    rows=[json.loads(line) for line in (root/'journal').read_text().splitlines()]
    pressure=[row for row in rows if 'boost_candidate' in row]
    rendered=[row for row in rows if row.get('v2_frame')]
    assert rendered
    if mode in ('paired','yield'):assert all(row['boost_visible'] and 0<row['boost_psi']<.01 for row in rendered)
    else:assert all(not row['boost_visible'] and row['boost_psi'] is None for row in rendered)
    if mode=='rpm-only':assert server.pressures==0 and not pressure
    elif mode in ('paired','yield'):assert all(row['boost_candidate'] for row in pressure) and len(pressure)>=(2 if mode=='yield' else 4)
    else:assert len(pressure)==3 and all(not row['boost_candidate'] for row in pressure) and server.pressures==3
    report.update(case=mode,pressure_requests=server.pressures,rpm_requests=server.rpms);results.append(report)
    (out/(mode+'.json')).write_text(json.dumps(report,indent=2));(out/(mode+'.jsonl')).write_text((root/'journal').read_text())
   finally:server.close()
 (out/'summary.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
