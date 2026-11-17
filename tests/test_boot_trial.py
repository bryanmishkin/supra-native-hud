import unittest,tempfile,subprocess,os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class BootTrial(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.p=Path(self.temp.name).resolve();self.root=self.p/'boot';self.root.mkdir(mode=0o700);self.factory=self.p/'factory';self.gate=self.p/'gate';self.target=self.p/'NavigationEceUsa.cfg';self.tx=self.p/'tx'
  self.factory.write_text('#!/usr/bin/env python3\nimport os,sys,json\nprint(json.dumps({"pid":os.getpid(),"cwd":os.getcwd(),"argv":sys.argv[1:],"preload":os.getenv("LD_PRELOAD"),"handoff":os.getenv("SUPRA_HUD_HANDOFF"),"kept":os.getenv("PRESERVED")}))\n');self.factory.chmod(0o700)
  subprocess.run(['cc','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-DSUPRA_BOOT_ROOT="'+str(self.root)+'"','-DSUPRA_FACTORY_PATH="'+str(self.factory)+'"',str(ROOT/'tools/boot_trial_gate.c'),'-o',str(self.gate)],check=True,capture_output=True)
  subprocess.run(['cc','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-DSUPRA_STARTUP_TARGET="'+str(self.target)+'"',str(ROOT/'tools/startup_file_transaction.c'),'-o',str(self.tx)],check=True,capture_output=True)
  self.env=os.environ.copy();self.env.pop('LD_PRELOAD',None);self.env['PRESERVED']='factory environment';(self.root/'libsupra-navigation-handoff-experimental.so').write_bytes(b'test-only')
 def tearDown(self):self.temp.cleanup()
 def run_gate(self):
  proc=subprocess.Popen([str(self.gate),'--config=original','argument with spaces'],cwd=self.p,env=self.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);out,err=proc.communicate(timeout=5);self.assertEqual(proc.returncode,0,err);r=json.loads(out);self.assertEqual(r['pid'],proc.pid);self.assertEqual(r['argv'],['--config=original','argument with spaces']);self.assertEqual(r['cwd'],str(self.p));self.assertEqual(r['kept'],'factory environment');return r
 def arm(self):
  (self.root/'armed').write_text('SUPRA-BOOT-TRIAL-1\n');(self.root/'armed').chmod(0o600)
 def test_default_and_one_use(self):
  self.assertIsNone(self.run_gate()['preload']);self.arm();self.assertIn('experimental.so',self.run_gate()['preload']);self.assertFalse((self.root/'armed').exists());self.assertTrue((self.root/'consumed').exists());self.assertIsNone(self.run_gate()['preload'])
 def test_disable_preserves_ticket(self):
  self.arm();(self.root/'disabled').touch();self.assertIsNone(self.run_gate()['preload']);self.assertTrue((self.root/'armed').exists())
 def test_existing_factory_preload_preserved(self):
  self.arm();self.env['LD_PRELOAD']='/test-existing-library';self.assertEqual(self.run_gate()['preload'],'/test-existing-library');self.assertTrue((self.root/'armed').exists())
 def test_bad_ticket_and_insecure_root(self):
  (self.root/'armed').write_text('wrong');self.assertIsNone(self.run_gate()['preload']);self.arm();self.root.chmod(0o777);self.assertIsNone(self.run_gate()['preload'])
 def test_symlink_ticket_refused(self):
  token=self.p/'ticket';token.write_text('SUPRA-BOOT-TRIAL-1\n');(self.root/'armed').symlink_to(token);self.assertIsNone(self.run_gate()['preload'])
 def test_existing_consumption_refused(self):
  self.arm();(self.root/'consumed').write_text('previous');self.assertIsNone(self.run_gate()['preload'])
 def test_transaction_preserves_original_inode_and_alias(self):
  before=self.p/'before';after=self.p/'after';before.write_text('original\n');after.write_text('candidate\n');self.target.write_bytes(before.read_bytes());self.target.chmod(0o640);alias=self.p/'alias';os.link(self.target,alias);ino=self.target.stat().st_ino
  subprocess.run([str(self.tx),'apply',str(before),str(after)],check=True,capture_output=True);self.assertEqual(self.target.read_bytes(),after.read_bytes());self.assertEqual(alias.read_bytes(),before.read_bytes());self.assertEqual(self.target.stat().st_mode&0o777,0o640)
  subprocess.run([str(self.tx),'rollback',str(before),str(after)],check=True,capture_output=True);self.assertEqual(self.target.stat().st_ino,ino);self.assertEqual(self.target.stat().st_nlink,2)
 def test_transaction_refuses_independent_edit(self):
  before=self.p/'before';after=self.p/'after';before.write_text('original');after.write_text('candidate');self.target.write_bytes(before.read_bytes());subprocess.run([str(self.tx),'apply',str(before),str(after)],check=True,capture_output=True);self.target.write_text('other edit');r=subprocess.run([str(self.tx),'rollback',str(before),str(after)],capture_output=True);self.assertNotEqual(r.returncode,0);self.assertEqual(self.target.read_text(),'other edit')
 def test_transaction_refuses_symlink(self):
  before=self.p/'before';after=self.p/'after';before.write_text('original');after.write_text('candidate');self.target.symlink_to(before);r=subprocess.run([str(self.tx),'apply',str(before),str(after)],capture_output=True);self.assertNotEqual(r.returncode,0);self.assertEqual(before.read_text(),'original')

 def test_concurrent_gate_consumes_only_once(self):
  self.arm();procs=[subprocess.Popen([str(self.gate)],cwd=self.p,env=self.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)];results=[]
  for proc in procs:
   out,err=proc.communicate(timeout=5);self.assertEqual(proc.returncode,0,err);results.append(json.loads(out))
  self.assertEqual(sum(x['preload'] is not None for x in results),1)
