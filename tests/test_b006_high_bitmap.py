import sys,unittest,struct
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from b006_high_bitmap import build_candidate
from ric_graph import decode_graph_body

class CandidateTests(unittest.TestCase):
 def allocation(self):return dict(handle=200,dimensions=[150,36],resource_id=0x01000009,models={10:0x0a000004,15:0x0f000004,17:0x11000000,29:0x1d00001d,34:0x22000004})
 def support(self):
  current=bytearray(59);struct.pack_into('>d',current,38,1000)
  return dict(support_start=[(10,current.hex()),(10,'0102')],position_start='0304',position_stop='0506')
 def test_single_parameter_pair_and_isolated_field(self):
  with patch('b006_high_bitmap.measured_support',return_value=self.support()):
   a=build_candidate(b'fixture',self.allocation(),threshold=92.0);b=build_candidate(b'fixture',self.allocation(),threshold=1000.0)
  self.assertEqual(a['setup'][1:],b['setup'][1:]);self.assertEqual(a['setup'][0][1][:38],b['setup'][0][1][:38]);self.assertEqual(a['setup'][0][1][46:],b['setup'][0][1][46:])
  d=decode_graph_body(10,b['setup'][3][1])['description']
  self.assertEqual(d['coming_road_id'],0xffffffff);self.assertEqual(d['current_state_id'],0x22000004);self.assertEqual(d['distance_id'],0x1d00001d)
  self.assertFalse(b['larger_extent_proven'])
 def test_wrong_profile_rejected(self):
  with self.assertRaises(ValueError):build_candidate(b'wrong',self.allocation(),threshold=1000)
 def test_invalid_admission(self):
  for key,value in [('handle',201),('dimensions',[320,200]),('resource_id',0x02000004),('models',{})]:
   a=self.allocation();a[key]=value
   with self.assertRaises(ValueError):build_candidate(b'',a,threshold=1000)
 def test_unknown_threshold(self):
  with self.assertRaises(ValueError):build_candidate(b'',self.allocation(),threshold=500)
if __name__=='__main__':unittest.main()
