import sys,unittest,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from capture_cold_start import classify
from repair_clean_rpm_disable import eligible
class ColdStart(unittest.TestCase):
 def test_different_faults_are_not_silently_recovered(self):
  for reason in [b'worker exit/cleanup uncertain\n',b'Disabled by operator\n',b'capture loss\n']:
   self.assertFalse(classify({'disabled':reason})['clean_rpm_match'])
  self.assertTrue(classify({'disabled':b'clean I/O retry budget exhausted\n'})['clean_rpm_match'])
 def test_unknown_and_runtime_states_are_distinguished(self):
  self.assertEqual(classify({})['state'],'no_runtime_status')
  self.assertEqual(classify({'acceptance.json':b'{"worker_running":false,"available":false}'})['state'],'resident_standby')
  self.assertEqual(classify({'acceptance.json':b'{"worker_running":true}'})['state'],'worker_reported_running')
 def test_repair_requires_complete_matched_target_evidence(self):
  c={'head':'169.254.199.119','read_only':True,'initial_classification':{'state':'persistently_disabled','clean_rpm_match':True},'gold_master_comparison':{str(i):{'matches':True} for i in range(15)}}
  self.assertTrue(eligible(c,c['head']));self.assertFalse(eligible(c,'169.254.199.99'))
  c['gold_master_comparison']['0']['matches']=False;self.assertFalse(eligible(c,c['head']))
 def test_tools_default_to_offline(self):
  tools=Path(__file__).resolve().parents[1]/'tools'
  for name in ['capture_cold_start.py','repair_clean_rpm_disable.py']:
   p=subprocess.run([sys.executable,str(tools/name)],capture_output=True,text=True,check=True)
   self.assertTrue(p.stdout)
if __name__=='__main__':unittest.main()

class RepairTransaction(unittest.TestCase):
 def exercise(self,fail_stage=False):
  import tempfile,hashlib,types,shlex
  from unittest.mock import patch
  import repair_clean_rpm_disable as repair
  from prepare_persistent import TARGETS
  class RemoteFixture:
   def __init__(self):self.files={};self.writable=False;self.failed=False
   def run(self,c,data=None):
    code=0;out=b'';words=shlex.split(c)
    if c=='uname -a':out=b'QNX hu-omap 6.5.0 armle'
    elif c.startswith('mount -u'):self.writable=c.startswith('mount -uw')
    elif c=='df -g /fs/sda0':out=b'rw' if self.writable else b'rdonly'
    elif c.startswith('slay -p '):code=1
    elif c.startswith('[ ! -S '):pass
    elif c.startswith('[ ! -e '):code=int(words[3] in self.files)
    elif c.startswith('cat '):
     code=int(words[1] not in self.files);out=self.files.get(words[1],b'')
    elif c.startswith('set -C;'):
     dest=words[-1]
     if fail_stage and dest.endswith('supra-nav-start-qnx.cold-start-new') and not self.failed:
      self.failed=True;self.files[dest]=b'partial';code=1
     elif dest in self.files:code=1
     else:self.files[dest]=data
    elif c.startswith('chmod '):pass
    elif c.startswith('mv '):self.files[words[2]]=self.files.pop(words[1])
    elif c=='sync':pass
    else:raise AssertionError(c)
    return types.SimpleNamespace(returncode=code,stdout=out,stderr=b'fixture failure' if code else b'')
  with tempfile.TemporaryDirectory() as temp:
   base=Path(temp);kit=base/'kit';gold=kit/'gold-master';gold.mkdir(parents=True);cap=base/'capture';cap.mkdir()
   old={};new={};remote=RemoteFixture()
   names=list(repair.REPLACEMENTS)+['nav-after.cfg','system-after.cfg']
   for name in names:
    body=('old '+name).encode();(gold/name).write_bytes(body);old[name]=hashlib.sha256(body).hexdigest();remote.files[repair.REPLACEMENTS.get(name,repair.ROOT+'/'+name)]=body
   for name in repair.REPLACEMENTS:
    body=('new '+name).encode();(kit/name).write_bytes(body);new[name]=hashlib.sha256(body).hexdigest()
   for name,(path,*_) in TARGETS.items():remote.files[path]=(gold/(name+'-after.cfg')).read_bytes()
   remote.files[repair.ROOT+'/disabled']=repair.REASON;remote.files[repair.ROOT+'/enabled']=b'SUPRA-PERSISTENT-1\n'
   checks={name:{'matches':True} for name in set(old)|{'nav-startup','system-startup'}}
   capture={'head':'169.254.199.119','read_only':True,'gold_master_comparison':checks,'initial_classification':{'state':'persistently_disabled','clean_rpm_match':True}}
   (cap/'capture.json').write_text(json.dumps(capture));(cap/'release-disabled.stdout').write_bytes(repair.REASON)
   args=types.SimpleNamespace(kit=kit,capture=cap,output=base/'result',ssh_socket=base/'socket',head=capture['head'])
   with patch.object(repair,'Remote',return_value=remote),patch.object(repair,'manifest',side_effect=[(new,'new-hash'),(old,repair.GOLD)]),patch.object(repair,'eligible',return_value=True):
    if fail_stage:
     with self.assertRaises(RuntimeError):repair.execute(args)
     self.assertEqual(remote.files[repair.ROOT+'/disabled'],repair.REASON)
    else:
     repair.execute(args);self.assertNotIn(repair.ROOT+'/disabled',remote.files);self.assertEqual(remote.files[repair.ROOT+'/disabled.before-cold-start-fix'],repair.REASON)
   for name,path in repair.REPLACEMENTS.items():self.assertEqual(remote.files[path],((gold if fail_stage else kit)/name).read_bytes())
   self.assertFalse(remote.writable);self.assertEqual(remote.files[repair.ROOT+'/enabled'],b'SUPRA-PERSISTENT-1\n')
 def test_patch_verifies_then_archives_exact_latch(self):self.exercise()
 def test_partial_upload_restores_originals_and_retains_disable(self):self.exercise(True)
