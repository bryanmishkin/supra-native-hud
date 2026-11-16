import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_graph_audit import audit_stream
from ric_graph import encode_list_state_body,encode_description_body
from ric_guiding import encode_high_roundabout_body
from ric_resource import encode_bitmap_body

def packet(method,body,client=1):
    return struct.pack('>HHIHHBBBB',0xb006,method,len(body)+8,client,1,1,1,0,0)+body

def state(active=20,handle=10):
    return packet(9,encode_list_state_body(handle,11,33,active_maneuver_id=active,passive_maneuver_id=0xffffffff,guidance_state=2 if active!=0xffffffff else 5,expected_arrival_time=0,total_delay_time=0,route_length=0,icon_resource_id=0xffffffff))

def description(handle=10):
    return packet(10,encode_description_body(handle,20,15,is_passive=False,previous_joined=False,previous_maneuver_id=0xffffffff,next_joined=False,next_maneuver_id=0xffffffff,maneuver_direction=0,current_state_id=0xffffffff,coming_road_id=0xffffffff,detailed_maneuver_id=30,distance_id=0xffffffff,navigation_event_ids=[],lane_guiding_ids=[],point_of_interest_ids=[]))

class GraphAuditTests(unittest.TestCase):
    def test_synthetic_chain_and_cancel(self):
        stream=state()+description()+packet(11,encode_high_roundabout_body(10,30,1,0,1,40))+packet(3,encode_bitmap_body(10,40,1,[1,1],b'x'))
        r=audit_stream(stream)
        self.assertEqual(r['events'][-1]['status'],'bitmap reference chain present')
        self.assertFalse(r['live_drawing_allowed'])
        r=audit_stream(stream+state(0xffffffff))
        self.assertEqual(r['events'][-1]['status'],'no active maneuver reference')
        self.assertFalse(r['remote_cleanup_proven'])
    def test_no_handle_cross_join(self):
        r=audit_stream(description(99)+state())
        self.assertEqual(r['events'][-1]['status'],'description missing or untraced')
    def test_no_client_cross_join(self):
        b=bytearray(description());b[8:10]=struct.pack('>H',2)
        r=audit_stream(bytes(b)+state())
        self.assertEqual(r['events'][-1]['status'],'description missing or untraced')
    def test_no_join_across_calls(self):
        audit_stream(description())
        self.assertEqual(audit_stream(state())['events'][-1]['status'],'description missing or untraced')
    def test_truncation_and_bad_extent(self):
        for b in (state()[:-1],state()+b'\0',state()[:4]+b'\0'*4+state()[8:]):
            with self.assertRaises(ValueError):audit_stream(b)
    def test_replaced_unknown_variant_invalidates_reference(self):
        r=audit_stream(description()+state()+packet(10,struct.pack('>IIBII',10,20,15,0,99)))
        self.assertEqual(r['events'][-1]['status'],'description missing or untraced')
    def test_identity_mismatch_rejected(self):
        b=bytearray(description());b[16+20]^=1
        with self.assertRaises(ValueError):audit_stream(bytes(b))

    def test_dispose_does_not_prove_erasure_or_reuse_old_graph(self):
        r=audit_stream(description()+state()+packet(7,struct.pack('>I',10))+state())
        self.assertEqual(r['events'][-1]['status'],'description missing or untraced')
        self.assertFalse(r['events'][-2]['remote_cleanup_proven'])
