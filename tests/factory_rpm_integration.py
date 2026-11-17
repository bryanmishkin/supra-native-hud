"""Factory feed must draw with zero diagnostic requests and clean up on feed loss."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
from standalone_integration import Servers
class NoGateway(Servers):
 def rpm(self,c):
  self.errors.append('unexpected diagnostic gateway request')
def run(exe,profile,out):
 results=[]
 for mode in ['normal','stale','unavailable']:
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);server=NoGateway('normal',root/'trigger');server.start();env=os.environ.copy()
   if mode!='normal':env['SUPRA_TEST_FEED_'+mode.upper()]='1'
   try:
    p=subprocess.run([str(exe.resolve()),'--parked-guidance-stopped',str(profile.resolve()),'127.0.0.1','127.0.0.1','127.0.0.1','test-only','1',str(root/'journal')],capture_output=True,text=True,env=env,timeout=6)
    report=json.loads(p.stdout);assert report['cleanup_verified'] and not server.resources and not server.errors,(p.stdout,p.stderr,server.errors)
    if mode=='normal':assert p.returncode==0 and report['frames']>=3
    else:assert p.returncode==2 and report['reason'].startswith('rpm_transport:factory feed')
    if mode=='unavailable':assert server.uploads==0
    if mode=='stale':assert server.uploads>0
    results.append(dict(case=mode,passed=True,report=report,diagnostic_requests=0))
   finally:server.close()
 out.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
if __name__=='__main__':run(*map(Path,sys.argv[1:]))
