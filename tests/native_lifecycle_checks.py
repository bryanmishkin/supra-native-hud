#!/usr/bin/env python3
import sys,tempfile,subprocess,json,os,time
from pathlib import Path
from standalone_integration import Servers
exe=Path(sys.argv[1]).resolve();control=Path(sys.argv[2]).resolve();profile=Path(sys.argv[3]).resolve();out=Path(sys.argv[4]);out.mkdir(exist_ok=False);results=[]
for case in ('self-check','disabled-before-start','disabled-active','control-stop','read-only-rpm'):
 with tempfile.TemporaryDirectory() as d:
  root=Path(d);server=Servers('normal',root/'unused');server.start();env=os.environ.copy();env['SUPRA_HUD_DISABLE_FILE']=str(root/'disabled')
  if case=='disabled-before-start':(root/'disabled').touch()
  args=[str(exe),'--parked-guidance-stopped',str(profile),'127.0.0.1','127.0.0.1','127.0.0.1','test-only','2',str(root/'journal')]
  if case=='self-check':args=[str(exe),'--self-check']
  if case=='read-only-rpm':args=[str(exe),'--probe-rpm','127.0.0.1','127.0.0.1']
  try:
   p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,text=True)
   if case in ('disabled-active','control-stop'):
    for _ in range(200):
     if server.uploads>=2:break
     time.sleep(.005)
    if case=='disabled-active':(root/'disabled').touch()
    else:subprocess.run([str(control),str(root/'journal')+'.handoff'],check=True,capture_output=True,timeout=6)
   stdout,stderr=p.communicate(timeout=13);assert p.returncode==0,(case,stdout,stderr);rows=[json.loads(x) for x in stdout.splitlines()];r=rows[-1]
   if case=='read-only-rpm':assert r['valid']==40 and r['hud_writes']==0 and len(rows)==41 and not server.requests
   elif case=='self-check':assert r['self_check'] and not server.requests
   else:
    assert r['cleanup_verified'] and not server.resources
    if case.startswith('disabled'):assert r['reason']=='disabled'
    if case=='disabled-before-start':assert not server.requests
    if case=='control-stop':assert r['reason']=='factory_navigation_request'
   results.append({'case':case,'passed':True,'result':r});(out/(case+'.stdout')).write_text(stdout)
  finally:server.close()
(out/'summary.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
