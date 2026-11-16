import unittest,tempfile,json,sys,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from validation_session import create,record,verify,GATES
from release_transaction import plan
class Deployment(unittest.TestCase):
 def test_gate_invalidation_and_kit_identity(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);kit=p/'kit';kit.write_bytes(b'v1');e=p/'evidence';e.write_text('operator observation and saved output');session=p/'session';create(session,kit)
   with self.assertRaises(ValueError):record(session,kit,'install_v1',e,True,'premature')
   for gate in GATES:record(session,kit,gate,e,True,'synthetic test only')
   self.assertTrue(verify(session,kit))
   record(session,kit,'native_display',e,False,'display failed');self.assertFalse(verify(session,kit))
   self.assertNotIn('install_v1',json.loads((session/'session.json').read_text())['gates'])
   kit.write_bytes(b'v2')
   with self.assertRaises(ValueError):record(session,kit,'identity',e,True,'wrong kit')
 def test_evidence_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);kit=p/'kit';kit.write_bytes(b'v1');e=p/'e';e.write_text('evidence');session=p/'s';create(session,kit)
   for gate in GATES:record(session,kit,gate,e,True,'synthetic')
   (session/'identity-evidence').write_text('changed');self.assertFalse(verify(session,kit))
 def test_transaction_rehearsal(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);old=p/'old';new=p/'new';old.write_text('original\n');new.write_text('reviewed candidate\n');target=p/'starter.cfg';target.write_bytes(old.read_bytes());target.chmod(0o640);out=p/'tx'
   plan('/opt/sys/etc/starter.cfg',old,new,out)
   # Remap only the destination directory for a local filesystem rehearsal.
   for action in ('apply','rollback'):
    script=out/(action+'.sh');script.write_text(script.read_text().replace('/opt/sys/etc',str(p)))
   subprocess.run(['sh',str(out/'apply.sh')],check=True,capture_output=True);self.assertEqual(target.read_bytes(),new.read_bytes());self.assertEqual(target.stat().st_mode&0o777,0o640)
   target.write_text('independent edit\n');r=subprocess.run(['sh',str(out/'rollback.sh')],capture_output=True);self.assertNotEqual(r.returncode,0);self.assertEqual(target.read_text(),'independent edit\n')
   target.write_bytes(new.read_bytes());subprocess.run(['sh',str(out/'rollback.sh')],check=True,capture_output=True);self.assertEqual(target.read_bytes(),old.read_bytes())
 def test_unreviewed_target(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   with self.assertRaises(ValueError):plan('/etc/anything',p/'x',p/'y',p/'z')
 def test_service_switch_and_uncertain_stop(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);root=p/'app';state=p/'ram';root.mkdir();state.mkdir();service=ROOT/'deployment/hud-service.sh';switch=ROOT/'deployment/switch-release.sh'
   for rel in ('aaaa','bbbb'):
    folder=root/'releases'/rel;folder.mkdir(parents=True);(folder/'release.ok').write_text(rel+'\n')
    control=folder/'supra-hud-control-qnx';control.write_text('#!/bin/sh\nexit 2\n');control.chmod(0o700)
   (root/'current').write_text('aaaa\n');(root/'enabled').touch()
   subprocess.run(['sh',str(service),str(root),str(state),'startup'],check=True)
   self.assertFalse((state/'lock').exists())
   subprocess.run(['sh',str(switch),str(root),str(state),'activate','bbbb'],check=True,capture_output=True)
   self.assertEqual((root/'current').read_text().strip(),'bbbb');self.assertTrue((root/'disabled').exists())
   subprocess.run(['sh',str(switch),str(root),str(state),'rollback'],check=True,capture_output=True);self.assertEqual((root/'current').read_text().strip(),'aaaa')
   (state/'lock').mkdir()
   r=subprocess.run(['sh',str(switch),str(root),str(state),'activate','bbbb'],capture_output=True);self.assertNotEqual(r.returncode,0);self.assertEqual((root/'current').read_text().strip(),'aaaa')
 def test_factory_wrapper_preserves_args_and_defaults(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);root=p/'app';state=p/'ram';root.mkdir();state.mkdir();factory=p/'factory';factory.write_text('#!/bin/sh\nprintf "%s\\n" "$PWD" "$*" "${LD_PRELOAD:-none}" "${SUPRA_HUD_HANDOFF:-none}"\n');factory.chmod(0o700)
   wrapper=p/'wrapper';wrapper.write_text((ROOT/'deployment/factory-controller-wrapper.sh').read_text().replace('/var/opt/supra-hud',str(root)).replace('/dev/shmem/supra-hud',str(state)).replace('/opt/nav/eceusa/bin/NavNBTEvoController',str(factory)));wrapper.chmod(0o700)
   env=os.environ.copy();env.pop('LD_PRELOAD',None);env.pop('SUPRA_HUD_HANDOFF',None)
   def run():return subprocess.check_output([str(wrapper),'--config=original.ini','argument with spaces'],cwd=p,env=env,text=True).splitlines()
   self.assertEqual(run()[:3],[str(p.resolve()),'--config=original.ini argument with spaces','none'])
   folder=root/'releases'/'aaaa';folder.mkdir(parents=True);(root/'current').write_text('aaaa\n');(folder/'release.ok').write_text('aaaa\n');(root/'factory-hook.enabled').write_text('aaaa\n');(folder/'libsupra-navigation-handoff-experimental.so').touch()
   self.assertEqual(run()[2:], [str(folder/'libsupra-navigation-handoff-experimental.so'),str(state/'active.jsonl.handoff')])
   (root/'disabled').touch();self.assertEqual(run()[2],'none')
