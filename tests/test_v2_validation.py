import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import prepare_v2_test as prep
import run_v2_validation as runner
class V2Preparation(unittest.TestCase):
 def test_restoration_requires_live_samples_not_only_heartbeat(self):
  before=runner.rpm_progress(b'{"rpm":650,"frame":10,"sample_ms":1000}\n{"partial":')
  runner.require_rpm_advance(before,{'rpm':650,'frame':11,'sample_ms':1250})
  for after in [before,{'rpm':650,'frame':11,'sample_ms':1000},{'rpm':650,'frame':1,'sample_ms':1250}]:
   with self.assertRaises(ValueError):runner.require_rpm_advance(before,after)
  with self.assertRaises(ValueError):runner.rpm_progress(b'{"heartbeat":2000}\n')
 def test_native_worker_result_preamble(self):
  row=b'[DsiClient] ATTACHED to server\n{"reason":"duration_complete","cleanup_verified":true,"shared_instance_preserved":true}\n'
  self.assertTrue(runner.worker_result(row)['cleanup_verified'])
  with self.assertRaises(ValueError):runner.worker_result(b'unexpected\n'+row)
 def fixture(self,root):
  old=root/'v1';old.mkdir();(old/'supra-profile.bin').write_bytes(b'private-fixture')
  (old/'manifest.json').write_text(json.dumps({'sha256':{'supra-profile.bin':hashlib.sha256(b'private-fixture').hexdigest()}}))
  digest=hashlib.sha256((old/'manifest.json').read_bytes()).hexdigest()
  binary=root/'worker';binary.write_bytes(b'candidate-fixture')
  audit=root/'audit.json';audit.write_text(json.dumps({'static_gate_passed':True,'candidate':{'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}}))
  return old,digest,binary,audit
 def test_hash_pinned_packaging_and_unchanged_original(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);old,digest,binary,audit=self.fixture(root);before=(old/'manifest.json').read_bytes()
   with patch.object(prep,'ACCEPTED_V1_KIT',digest):data=prep.prepare(binary,audit,old,root/'kit')
   self.assertEqual((old/'manifest.json').read_bytes(),before)
   self.assertEqual((root/'kit/v1-accepted-kit/manifest.json').read_bytes(),before)
   self.assertEqual(data['v1_kit_sha256'],digest);self.assertFalse(data['car_tested'])
 def test_wrong_gold_or_stale_binary_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);old,digest,binary,audit=self.fixture(root)
   with self.assertRaises(ValueError):prep.prepare(binary,audit,old,root/'wrong')
   binary.write_bytes(b'changed')
   with patch.object(prep,'ACCEPTED_V1_KIT',digest),self.assertRaises(ValueError):prep.prepare(binary,audit,old,root/'stale')
   self.assertFalse((root/'stale').exists())
 def test_default_plan_never_needs_socket_or_kit(self):
  tool=Path(runner.__file__)
  for phase in runner.PHASES:
   p=subprocess.run([sys.executable,str(tool),phase],capture_output=True,text=True,check=True)
   data=json.loads(p.stdout);self.assertFalse(data['network']);self.assertFalse(data['installed_files_changed'])
 def test_missing_current_confirmation_stops_before_target_command(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);old,digest,binary,audit=self.fixture(root)
   with patch.object(prep,'ACCEPTED_V1_KIT',digest):prep.prepare(binary,audit,old,root/'kit')
   _,kit_hash=runner.manifest(root/'kit');out=root/'out';out.mkdir()
   (out/'v2-session.json').write_text(json.dumps({'kit':kit_hash,'head':'169.254.199.119','phases':{'preflight':True}}))
   a=SimpleNamespace(phase='pause-v1',kit=root/'kit',output=out,head='169.254.199.119',ssh_socket=root/'socket',guidance_stopped=False)
   with patch.object(runner,'ACCEPTED_V1_KIT',digest),patch.object(runner,'Remote') as remote,self.assertRaises(ValueError):runner.execute(a)
   remote.return_value.run.assert_not_called()
if __name__=='__main__':unittest.main()
