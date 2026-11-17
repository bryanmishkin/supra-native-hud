import unittest,tempfile,subprocess,sys,json,hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import persistent_install as install
REPO=Path(__file__).resolve().parents[1]
class Installer(unittest.TestCase):
 def test_second_config_failure_restores_both_and_readonly(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);kit=p/'kit';kit.mkdir();out=p/'out';out.mkdir();root=p/'v1';ram=p/'ram';nav=p/'nav.cfg';system=p/'system.cfg';nav.write_bytes(b'nav-original\n');system.write_bytes(b'system-original\n')
   targets={'nav':(str(nav),'old',str(p/'nav-gate'),'partition','2'),'system':(str(system),'old',str(p/'hmi-gate'),'partition','17')}
   for name,target in [('nav',nav),('system',system)]:
    (kit/(name+'-before.cfg')).write_bytes(target.read_bytes());(kit/(name+'-after.cfg')).write_bytes((name+'-changed\n').encode())
    binary='supra-'+('startup' if name=='nav' else 'system')+'-transaction-qnx'
    subprocess.run(['cc','-DSUPRA_STARTUP_TARGET="'+str(target)+'"',str(REPO/'tools/startup_file_transaction.c'),'-o',str(kit/binary)],check=True,capture_output=True)
   for name in ['supra-nav-start-qnx','supra-hmi-start-qnx']:(kit/name).write_bytes(b'fixture')
   (kit/'supra-persistent-state-qnx').write_text('#!/bin/sh\necho disabled > "'+str(root)+'/disabled"\necho STATE_SAVED\n')
   (kit/'manifest.json').write_text(json.dumps({'sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in kit.iterdir()}}))
   digest=hashlib.sha256((kit/'manifest.json').read_bytes()).hexdigest();(out/'installer.json').write_text(json.dumps({'kit':digest,'head':'169.254.199.119','phases':{'preflight':True},'applied':[]}))
   class Fake:
    writable=False
    def __init__(self,*args):pass
    def run(self,c,data=None):
     if c.startswith('mount -u'):Fake.writable=c.startswith('mount -uw');return subprocess.CompletedProcess([],0,b'',b'')
     if c=='df -g /fs/sda0':return subprocess.CompletedProcess([],0,b'Flags: '+(b'noatime' if Fake.writable else b'noatime, rdonly'),b'')
     if 'supra-system-transaction-qnx apply' in c:return subprocess.CompletedProcess([],2,b'',b'injected second-file failure')
     return subprocess.run(['sh','-c',c],input=data,capture_output=True)
   a=SimpleNamespace(phase='install',kit=kit,output=out,ssh_socket=p/'sock',head='169.254.199.119')
   with patch.object(install,'Remote',Fake),patch.object(install,'ROOT',str(root)),patch.object(install,'STATE',str(ram)),patch.object(install,'TARGETS',targets):
    with self.assertRaises(RuntimeError):install.execute(a)
    self.assertFalse(Fake.writable);self.assertEqual(nav.read_bytes(),b'nav-changed\n');self.assertEqual(system.read_bytes(),b'system-original\n')
    a.phase='rollback';s=install.execute(a)
    Path(s['boundary']).unlink();self.assertTrue(s['phases']['rollback']);self.assertFalse(Fake.writable);self.assertEqual(nav.read_bytes(),b'nav-original\n');self.assertEqual(system.read_bytes(),b'system-original\n')
if __name__=='__main__':unittest.main()
