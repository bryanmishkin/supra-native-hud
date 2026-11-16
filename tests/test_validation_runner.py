import unittest,tempfile,json,hashlib,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import run_v1_validation as runner
class Runner(unittest.TestCase):
 def kit(self,p):
  p.mkdir();worker='''#!/bin/sh
case "$1" in
--self-check) echo '{"self_check":true}';;
--probe-rpm)
'''+''.join("echo '{\"rpm\":650,\"sample_ms\":%d,\"latency_ms\":1}'\n"%i for i in range(40))+'''echo '{"rpm_probe_passed":true,"valid":40,"hud_writes":0}';;
*) echo '{}' > "$8"; case "$8" in *yield*) reason=factory_navigation_request;; *) reason=duration_complete;; esac
 echo "{\\"cleanup_verified\\":true,\\"shared_instance_preserved\\":true,\\"reason\\":\\"$reason\\"}";;
esac
'''
  data={'supra-standalone-parked-qnx':worker,'run-isolated-handoff-selftest.sh':"#!/bin/sh\necho 'PASS: isolated pre-send hook ABI and CLEAN handshake'\n",'supra-hud-control-qnx':'#!/bin/sh\necho CLEAN\n','supra-profile.bin':'fixture','preflight-startup.sh':'# read-only fixture'}
  for name,value in data.items():(p/name).write_text(value)
  (p/'manifest.json').write_text(json.dumps({'sha256':{n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in data}}))
 def test_full_local_rehearsal_and_retry(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);kit=root/'kit';self.kit(kit);remote_root=root/'fake-target';remote_root.mkdir();output=root/'session'
   class FakeRemote:
    def __init__(self,*args):pass
    def run(self,command,data=None,timeout=50):
     if command=='sh':return subprocess.CompletedProcess([],0,b'QNX hu-omap 6.5.0 ARM armle\n',b'')
     command=command.replace('/dev/shmem',str(remote_root))
     return subprocess.run(['sh','-c',command],input=data,capture_output=True,timeout=timeout)
   args=SimpleNamespace(kit=kit,output=output,phase='preflight',ssh_socket=root/'none',head='169.254.199.119',guidance_stopped=True,visual_cleanup_confirmed=True)
   with patch.object(runner,'Remote',FakeRemote):
    for phase in ('preflight','stage','isolated','rpm','draw','draw','yield','collect','remove'):
     args.phase=phase;state=runner.execute(args);self.assertTrue(state['phases'][phase])
    self.assertEqual(state['attempts']['draw'],2);self.assertFalse(list(remote_root.iterdir()))
    self.assertTrue((output/'draw-01.stdout').exists());self.assertTrue((output/'draw-02.stdout').exists())
 def test_hash_rejects_before_network(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);kit=p/'kit';self.kit(kit);(kit/'supra-profile.bin').write_text('tampered')
   a=SimpleNamespace(kit=kit,output=p/'out',phase='preflight')
   with patch.object(runner,'Remote') as remote:
    with self.assertRaises(ValueError):runner.execute(a)
    remote.assert_not_called()
 def test_prerequisite_rejects_before_network(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);kit=p/'kit';self.kit(kit);out=p/'out';out.mkdir();_,digest=runner.manifest(kit);(out/'runner-state.json').write_text(json.dumps({'kit_sha256':digest,'head':'169.254.199.119','phases':{}}))
   a=SimpleNamespace(kit=kit,output=out,phase='draw',head='169.254.199.119',guidance_stopped=True)
   with patch.object(runner,'Remote') as remote:
    with self.assertRaises(ValueError):runner.execute(a)
    remote.assert_not_called()
