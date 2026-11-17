#!/usr/bin/env python3
"""Run inside isolated Linux build container; fake factory only."""
import os,socket,subprocess,threading,tempfile,time,json,sys,select
from pathlib import Path
out=Path(sys.argv[1]);results=[]
for case in ('clean','null-destination','uncertain','timeout','absent','non-hud','keepalive','other-destination','disabled'):
 with tempfile.TemporaryDirectory() as temp:
  path=str(Path(temp)/'handoff');s=socket.socket(socket.AF_UNIX);s.bind(path);s.listen();s.settimeout(.25)
  trace=Path(temp)/'trace.log';env=os.environ.copy();env.update(LD_PRELOAD=str(out/'libhandoff.so'),SUPRA_HUD_HANDOFF=path,SUPRA_HUD_TRACE_FILE=str(trace))
  if case=='absent':s.close();os.unlink(path)
  if case=='disabled':
   disable=Path(temp)/'disabled';disable.touch();env['SUPRA_HUD_DISABLE_FILE']=str(disable)
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
  events=[line.split()[-1] for line in trace.read_text().splitlines()] if trace.exists() else []
  if case in ('clean','null-destination'):assert events==['HANDOFF_CHECK','CLEAN','FACTORY_SEND'],events
  elif case in ('uncertain','timeout'):assert events==['HANDOFF_CHECK','UNCERTAIN','FACTORY_SEND'],events
  elif case=='absent':assert events==['HANDOFF_CHECK','FACTORY_SEND'],events
  else:assert not events,events
  results.append(dict(case=case,passed=True,elapsed_seconds=round(elapsed,3)));s.close()
(out/'hook-tests.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
# Exercise the actual persistent pre-send framing, not just the legacy stop socket.
with tempfile.TemporaryDirectory() as temp:
 path=str(Path(temp)/'broker');s=socket.socket(socket.AF_UNIX);s.bind(path);s.listen();s.settimeout(2)
 trace=Path(temp)/'broker-trace';env=os.environ.copy();role=env.get('SUPRA_TEST_ROLE','nav')
 env.update(LD_PRELOAD=str(out/'libhandoff.so'),SUPRA_HUD_HANDOFF=str(Path(temp)/'worker'),SUPRA_HUD_BROKER_SOCKET=path,SUPRA_HUD_FACTORY_ROLE=role,SUPRA_HUD_TRACE_FILE=str(trace))
 p=subprocess.Popen([str(out/'hook-driver'),'clean'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 c,_=s.accept();c.settimeout(2)
 def read(n):
  b=b''
  while len(b)<n:
   v=c.recv(n-len(b));assert v;b+=v
  return b
 h=read(12);assert h[:4]==b'PRE1' and h[4]==(role=='hmi') and h[5:8]==b'\0\0\0'
 n=int.from_bytes(h[8:12],'big');assert n==32;packet=read(n);assert packet[:2]==(b'\xb0\x0e' if role=='hmi' else b'\xb0\x06')
 assert not select.select([p.stdout],[],[],.05)[0]
 c.sendall(b'CLEAN\n');stdout,stderr=p.communicate(timeout=2);assert p.returncode==0 and stdout==b'FACTORY_SEND\n' and not stderr
 assert [line.split()[-1] for line in trace.read_text().splitlines()]==['HANDOFF_CHECK','BROKER_CLEAN','FACTORY_SEND']
 c.close();s.close();results.append({'case':'persistent-broker-clean','role':role,'passed':True})
(out/'hook-tests.json').write_text(json.dumps(results,indent=2));print('Persistent broker framing passed:',role)
