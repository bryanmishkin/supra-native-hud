import unittest,tempfile,subprocess,json,hashlib,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'tools'))
import boot_trial_session as b
class BootSession(unittest.TestCase):
 def test_complete_phases_and_reboot_gate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);kit=p/'kit';kit.mkdir();factory=p/'factory';factory.mkdir();persist=p/'persistent';persist.mkdir();ram=p/'ram';target=factory/'NavigationEceUsa.cfg';target.write_bytes(b'original\n')
   for name,data in [('before.cfg',b'original\n'),('after.cfg',b'candidate\n'),('libsupra-navigation-handoff-experimental.so',b'fixture'),('supra-boot-trial-gate-qnx',b'fixture'),('fake-factory-qnx',b'fixture')]: (kit/name).write_bytes(data)
   for name,path in [('supra-startup-rehearsal-qnx',ram/'fixture.cfg'),('supra-startup-transaction-qnx',target)]:subprocess.run(['cc','-DSUPRA_STARTUP_TARGET="'+str(path)+'"',str(REPO/'tools/startup_file_transaction.c'),'-o',str(kit/name)],check=True,capture_output=True)
   (kit/'supra-boot-gate-rehearsal-qnx').write_text('#!/bin/sh\ncd "${0%/*}"\nif [ -f armed ] && [ ! -f consumed ]; then mv armed consumed; echo "PRELOAD=/tmp/supra-boot-rehearsal/libsupra-navigation-handoff-experimental.so"; else echo PRELOAD=none; fi\necho "ARG=argument with spaces"\necho FAKE_FACTORY_ONLY\n')
   (kit/'manifest.json').write_text(json.dumps({'sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in kit.iterdir()}}))
   commands=[]
   class Fake:
    current='100';hook=False
    def __init__(self,*args):pass
    def run(self,cmd,data=None):
     commands.append(cmd)
     if cmd=='uname -a':return subprocess.CompletedProcess([],0,b'QNX hu-omap 6.5.0 armle\n',b'')
     if cmd=='slay -p NavNBTEvoController':return subprocess.CompletedProcess([],1,(self.current+'\n').encode(),b'')
     if cmd.startswith('pidin '):return subprocess.CompletedProcess([],0,b'ff-experimental.so' if cmd.endswith('mem') and self.hook else b'NavNBTEvoController',b'')
     if cmd.startswith('ls -ln '):return subprocess.CompletedProcess([],0,b'fixture mount',b'')
     mapped=cmd.replace('/opt/nav/eceusa/bin',str(factory)).replace('/var/opt/supra-hud',str(persist)).replace('/tmp/supra-boot-rehearsal',str(ram)).replace('/tmp/supra-hud-boottrial',str(p/'runtime')).replace('/tmp/supra-boot-boundary-',str(p/'boundary-'))
     return subprocess.run(['sh','-c',mapped],input=data,capture_output=True)
   a=SimpleNamespace(kit=kit,output=p/'out',head='169.254.199.119',ssh_socket=p/'sock',factory_normal=True)
   with patch.object(b,'Remote',Fake),patch.object(b.time,'sleep',lambda _:None):
    for phase in ['preflight','rehearse','configure']:
     a.phase=phase;b.execute(a)
    self.assertEqual(target.read_bytes(),b'candidate\n');a.phase='verify-baseline'
    with self.assertRaises(RuntimeError):b.execute(a)
    [f.unlink() for f in p.glob('boundary-*')];Fake.current='100';b.execute(a);a.phase='arm';b.execute(a)
    root=persist/'boot-trial';(root/'armed').rename(root/'consumed');[f.unlink() for f in p.glob('boundary-*')];Fake.current='300';Fake.hook=True;a.phase='verify-hook';b.execute(a)
    a.phase='rollback';b.execute(a);self.assertEqual(target.read_bytes(),b'original\n');[f.unlink() for f in p.glob('boundary-*')];Fake.current='400';Fake.hook=False;a.phase='verify-restored';result=b.execute(a);self.assertTrue(result['phases']['verify-restored'])
   self.assertFalse(any('kill ' in cmd or 'slay -s' in cmd or 'reboot' in cmd for cmd in commands))
