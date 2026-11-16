import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from factory_activity import FactoryActivity
from ric_graph import encode_list_state_body
class FactoryActivityTests(unittest.TestCase):
 def packet(self,state,client=12):
  b=encode_list_state_body(200,0x21000000,33,active_maneuver_id=0xffffffff,passive_maneuver_id=0xffffffff,guidance_state=state,expected_arrival_time=0,total_delay_time=0,route_length=0,icon_resource_id=0xffffffff)
  return struct.pack('>HHIHHBBBB',0xb006,9,len(b)+8,client,1,1,1,0,0)+b
 def test_idle_does_not_grant_shared_session_ownership(self):
  a=FactoryActivity();a.observe(self.packet(0),1000);self.assertEqual(a.snapshot(1000)['guidance'],'idle');self.assertTrue(a.blocks_drawing(1000));self.assertFalse(a.snapshot(1000)['drawing_allowed'])
 def test_own_packets_never_fake_factory_idle(self):
  a=FactoryActivity();a.observe(self.packet(2),1000);a.observe(self.packet(0,0x5348),1001);self.assertEqual(a.snapshot(1001)['guidance'],'active_or_transition');self.assertEqual(a.snapshot(1400)['guidance'],'unknown')
