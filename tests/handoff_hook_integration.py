#!/usr/bin/env python3
"""Run inside isolated Linux build container; fake factory only."""
import os,socket,subprocess,threading,tempfile,time,json,sys,select
from pathlib import Path
out=Path(sys.argv[1]);results=[]
for case in ('clean','null-destination','uncertain','timeout','absent','non-hud','keepalive','other-destination'):
 with tempfile.TemporaryDirectory() as temp:
  path=str(Path(temp)/'handoff');s=socket.socket(socket.AF_UNIX);s.bind(path);s.listen();s.settimeout(.25)
  env=os.environ.copy();env.update(LD_PRELOAD=str(out/'libhandoff.so'),SUPRA_HUD_HANDOFF=path)
  if case=='absent':s.close();os.unlink(path)
  start=time.monotonic();p=subprocess.Popen([str(out/'hook-driver'),case],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if case in ('clean','null-destination','uncertain','timeout'):
   c,_=s.accept();c.settimeout(1);request=c.recv(32);assert request==b'YIELD1\n',request
   # Factory send must remain blocked until reply (or bounded timeout).
   assert not select.select([p.stdout],[],[],.05)[0]
   if case in ('clean','null-destination'):c.sendall(b'CLEAN\n')
   elif case=='uncertain':c.sendall(b'UNCERTAIN\n')
   stdout,stderr=p.communicate(timeout=4);c.close()
  else:
   stdout,stderr=p.communicate(timeout=1)
   if case!='absent':
    try:c,_=s.accept();raise AssertionError('Unexpected handoff')
    except socket.timeout:pass
  elapsed=time.monotonic()-start;assert p.returncode==0 and stdout==b'FACTORY_SEND\n'
  if case in ('uncertain','timeout'):assert b'cleanup uncertain' in stderr
  else:assert stderr==b'',stderr
  if case=='timeout':assert 2.8<=elapsed<3.8
  results.append(dict(case=case,passed=True,elapsed_seconds=round(elapsed,3)));s.close()
(out/'hook-tests.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
