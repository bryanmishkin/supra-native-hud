import unittest,sys,tempfile,subprocess,os,socket,time,signal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from prepare_persistent import patch
REPO=Path(__file__).resolve().parents[1]
class Package(unittest.TestCase):
 def test_exact_entry_preserves_contract(self):
  for which,number,name,partition in [('nav','2','./NavNBTEvoController','softrt_NAV'),('system','17','/opt/hmi/bin/zipped/HmiMain3D','interaction')]:
   b=('<DynamicConfig><ProcessTable><Process><Number>'+number+'</Number><Name>'+name+'</Name><Partition>'+partition+'</Partition><Args>unchanged</Args><ResArgs>unchanged</ResArgs><Shutdown>IGNORE</Shutdown></Process></ProcessTable></DynamicConfig>').encode()
   a=patch(b,which);self.assertIn(b'<Shutdown>IGNORE</Shutdown>',a);self.assertNotEqual(a,b)
   with self.assertRaises(ValueError):patch(a,which)
   with self.assertRaises(ValueError):patch(b.replace(b'<Args>unchanged',b'<Args>different'),which)
 def test_gate_defaults_once_and_committed(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'release';state=Path(tmp)/'ram';root.mkdir(mode=0o700)
   fake=Path(tmp)/'factory';fake.write_text('#!/bin/sh\necho FACTORY\necho "$*"\necho "${SUPRA_HUD_FACTORY_ROLE:-none}"\n');fake.chmod(0o700)
   noop=Path(tmp)/'noop.c';noop.write_text('int harmless(void){return 0;}\n')
   subprocess.run(['cc','-shared','-fPIC',str(noop),'-o',str(root/'libsupra-navigation-handoff-experimental.so')],check=True,capture_output=True)
   supervisor=root/'supra-resident-qnx';supervisor.write_text('#!'+sys.executable+'\nimport socket,time,os,sys\nfrom pathlib import Path\np=Path(sys.argv[2]);s=socket.socket(socket.AF_UNIX);s.bind(str(p/"factory.sock"));s.listen();(p/"fake.pid").write_text(str(os.getpid()));(p/"ready").write_text("CAPTURE_READY\\n");time.sleep(15)\n');supervisor.chmod(0o700)
   for n in ['supra-standalone-parked-qnx','supra-profile.bin']:(root/n).write_bytes(b'fixture')
   gate=Path(tmp)/'gate';subprocess.run(['cc','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-DSUPRA_RELEASE="'+str(root)+'"','-DSUPRA_RUNTIME="'+str(state)+'"','-DSUPRA_FACTORY="'+str(fake)+'"',str(REPO/'tools/persistent_boot_gate.c'),'-o',str(gate)],check=True,capture_output=True)
   def call(env=None):return subprocess.run([str(gate),'arg with spaces'],capture_output=True,text=True,timeout=4,env=env)
   p=call();self.assertEqual(p.returncode,0);self.assertIn('none',p.stdout)
   (root/'armed').write_text('SUPRA-TRIAL-1\n')
   try:
    p=call();self.assertEqual(p.returncode,0);self.assertIn('\nnav\n',p.stdout);self.assertIn('arg with spaces',p.stdout);self.assertFalse((root/'armed').exists());self.assertTrue((root/'consumed').exists())
    p=call();self.assertIn('\nnav\n',p.stdout) # second factory gate shares this boot
    (state/'trial-boot').unlink();(state/'activating').rmdir()
    p=call();self.assertIn('none',p.stdout) # next boot cannot reuse consumed ticket
    (root/'enabled').write_text('SUPRA-PERSISTENT-1\n');p=call();self.assertIn('\nnav\n',p.stdout)
    env=os.environ.copy();env['LD_PRELOAD']='libEGL_X.gpp.so:libGLESv2_X_FORWARD.gpp.so:libKD_X.gpp.so'
    p=call(env);self.assertIn('none',p.stdout) # nav never accepts the HMI preload
    subprocess.run(['cc','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-DSUPRA_ROLE="hmi"','-DSUPRA_RELEASE="'+str(root)+'"','-DSUPRA_RUNTIME="'+str(state)+'"','-DSUPRA_FACTORY="'+str(fake)+'"',str(REPO/'tools/persistent_boot_gate.c'),'-o',str(gate)],check=True,capture_output=True)
    fake.write_text('#!/bin/sh\necho FACTORY\necho "${SUPRA_HUD_FACTORY_ROLE:-none}"\necho "$LD_PRELOAD"\n')
    p=call(env);self.assertIn('\nhmi\n',p.stdout);self.assertIn(str(root/'libsupra-navigation-handoff-experimental.so')+':'+env['LD_PRELOAD'],p.stdout)
    env['LD_PRELOAD']='unrecognized.so';p=call(env);self.assertIn('none',p.stdout);self.assertIn('unrecognized.so',p.stdout)
    (root/'disabled').write_text('stop');p=call();self.assertIn('none',p.stdout)
   finally:
    if (state/'fake.pid').exists():os.kill(int((state/'fake.pid').read_text()),signal.SIGTERM)
if __name__=='__main__':unittest.main()
