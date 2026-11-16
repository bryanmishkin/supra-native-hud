import sys,json,tempfile,hashlib,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_tachometer_trial import verified_frames,run,RPMS
class TachTrialTests(unittest.TestCase):
 def setup_frames(self,root):
  root.mkdir();raw=b'\0\0\0\xff'*5400
  frames=[]
  for rpm in RPMS:
   p=root/('%d.bgra'%rpm);p.write_bytes(raw)
   frames.append(dict(rpm=rpm,file=p.name,sha256=hashlib.sha256(raw).hexdigest()))
  (root/'frames.json').write_text(json.dumps(dict(synthetic=True,frames=frames)))
 def test_tampering_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'frames';self.setup_frames(p);(p/'1000.bgra').write_bytes(b'bad')
   with self.assertRaises(ValueError):verified_frames(p)
 def simulate(self,failure=None):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);frames=root/'frames';self.setup_frames(frames)
   args=types.SimpleNamespace(frames=frames,output=root/'run',create_response=Path('reply'),support_stream=Path('stream'),ssh_socket=Path('socket'),head='127.0.0.1')
   calls=[]
   def child(cmd):
    calls.append(cmd);out=Path(cmd[cmd.index('--output')+1]);out.mkdir()
    r=dict(status='awaiting_visual_verification',forward_cancelled=True,cleanup_steps=[dict(acknowledged=True)],cleanup=dict(resources=[dict(dispose_acknowledged=True,post_dispose_check=False)]))
    if failure=='absent':r['cleanup']['resources'][0]['post_dispose_check']=None
    if failure=='graph':r['cleanup_steps'][0]['acknowledged']=False
    if failure=='forward':r['forward_cancelled']=False
    if failure=='missing':r['cleanup']['resources']=[]
    (out/'result.json').write_text(json.dumps(r))
    return types.SimpleNamespace(wait=lambda:0)
   with patch('run_tachometer_trial.subprocess.Popen',side_effect=child),patch('run_tachometer_trial.time.sleep'):
    rc=run(args)
   report=json.loads((args.output/'result.json').read_text())
   return rc,calls,report
 def test_three_bounded_complete_cycles(self):
  rc,calls,r=self.simulate();self.assertEqual(rc,0);self.assertEqual(len(calls),3)
  self.assertFalse(r['visual_pass']);self.assertFalse(r['automatic_navigation_detection'])
  for c in calls:self.assertEqual(c[c.index('--window-seconds')+1],'3')
 def test_any_cleanup_uncertainty_blocks_next_frame(self):
  for fault in ('absent','graph','forward','missing'):
   with self.subTest(fault=fault):
    rc,calls,r=self.simulate(fault);self.assertEqual(rc,2);self.assertEqual(len(calls),1);self.assertEqual(r['status'],'stopped')
