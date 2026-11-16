import json,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from request_navigation_yield import request,check_yield,NavigationYield,handoff_ready
from ric_guiding import encode_empty_guiding_body,decode_guiding_body
class NavigationYieldTests(unittest.TestCase):
 def test_empty_variant_fixed_vector(self):
  b=encode_empty_guiding_body(200,0x0a000004,10)
  self.assertEqual(b,bytes.fromhex('000000c8 0a000004 0a 00000000 00000000'))
  self.assertEqual(decode_guiding_body(b)['variant_tag'],0)
  self.assertEqual(decode_guiding_body(b)['payload_bytes'],0)
 def test_request_only_active_window_and_exact_token(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'result.json').write_text(json.dumps({'status':'creating'}))
   with self.assertRaises(ValueError):request(p)
   (p/'result.json').write_text(json.dumps({'status':'observing_marker','live_rpm':True}));request(p)
   with self.assertRaises(NavigationYield):check_yield(p)
   (p/'navigation-yield.request').write_text('unexpected')
   with self.assertRaises(ValueError):check_yield(p)
 def test_no_ready_without_all_cleanup_evidence(self):
  r=dict(status='awaiting_visual_verification',stop_reason='factory_navigation_request',forward_cancelled=True,cleanup_steps=[dict(acknowledged=True)],cleanup=dict(shared_instance_preserved=True,resources=[dict(dispose_acknowledged=True,post_dispose_check=False)]))
  self.assertTrue(handoff_ready(r))
  for key,value in [('status','failed_or_interrupted'),('stop_reason','duration_complete'),('forward_cancelled',False)]:
   bad=dict(r);bad[key]=value;self.assertFalse(handoff_ready(bad))
  r['cleanup']['resources'][0]['post_dispose_check']=None;self.assertFalse(handoff_ready(r))
