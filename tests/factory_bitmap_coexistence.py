"""Exercise actual worker with factory slots populated using existing server."""
import json,subprocess,sys,tempfile,struct
from pathlib import Path
from standalone_integration import Servers
worker,profile,out=map(Path,sys.argv[1:]);results=[]
for occupied in [None,0x01000008,0x01000009]:
 with tempfile.TemporaryDirectory() as tmp:
  t=Path(tmp);server=Servers('normal',t/'trigger');factory={rid:b'unchanged-factory-image' for rid in range(0x01000000,0x01000008)}
  if occupied is not None:factory[occupied]=b'occupied-tach-slot'
  server.resources.update(factory);server.start()
  try:
   p=subprocess.run([str(worker.resolve()),'--parked-guidance-stopped',str(profile.resolve()),'127.0.0.1','127.0.0.1','127.0.0.1','test-only','1',str(t/'journal')],capture_output=True,text=True,timeout=8);v=json.loads(p.stdout)
   assert server.resources==factory and not server.errors
   if occupied is None:
    assert p.returncode==0 and v['frames']>1 and v['cleanup_verified']
    for method,body in server.requests:
     if method in (2,3,8):assert struct.unpack_from('>I',body,4)[0] in (0x01000008,0x01000009)
   else:
    assert p.returncode==2 and v['reason']=='bitmap pool in use' and v['frames']==0 and v['cleanup_verified']
    assert server.uploads==0 and all(m==2 for m,b in server.requests)
    assert ('0x%08x'%occupied) in p.stderr
   results.append({'occupied_tach_slot':occupied,'passed':True,'frames':v['frames'],'factory_images_preserved':True})
  finally:server.close()
out.write_text(json.dumps(results,indent=2));print(out.read_text())
