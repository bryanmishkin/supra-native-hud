import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_graph import decode_graph_body, decode_graph_packet, encode_list_state_body, encode_description_body, factory_state_transition_allowed

STATE=bytes.fromhex('01020304 11121314 21 0000002a 00000002 11121314 21 21222324 ffffffff 02 0000000000000055 0000000000000000 3ff8000000000000 ffffffff')
DESC=bytes.fromhex('01020304 21222324 0f 00000031 00000001 21222324 0f 00 01 31323334 00 ffffffff 08 41424344 51525354 61626364 71727374 00000004 81828384 00000000 00000000')

class GraphTests(unittest.TestCase):
    def test_fixed_state(self):
        self.assertEqual(encode_list_state_body(0x01020304,0x11121314,33,active_maneuver_id=0x21222324,passive_maneuver_id=0xffffffff,guidance_state=2,expected_arrival_time=85,total_delay_time=0,route_length=1.5,icon_resource_id=0xffffffff),STATE)
        r=decode_graph_body(9,STATE)['list_state']
        self.assertEqual((r['active_maneuver_id'],r['route_length'],r['guidance_state']),(0x21222324,1.5,2))
    def test_fixed_description(self):
        self.assertEqual(encode_description_body(0x01020304,0x21222324,15,is_passive=False,previous_joined=True,previous_maneuver_id=0x31323334,next_joined=False,next_maneuver_id=0xffffffff,maneuver_direction=8,current_state_id=0x41424344,coming_road_id=0x51525354,detailed_maneuver_id=0x61626364,distance_id=0x71727374,navigation_event_ids=[0x81828384],lane_guiding_ids=[],point_of_interest_ids=[]),DESC)
        r=decode_graph_body(10,DESC)['description']
        self.assertEqual(r['detailed_maneuver_id'],0x61626364)
        self.assertEqual(r['navigation_event_ids'],[0x81828384])
    def test_every_truncation(self):
        for method,body in ((9,STATE),(10,DESC)):
            for n in range(len(body)):
                with self.subTest(method=method,n=n),self.assertRaises(ValueError):decode_graph_body(method,body[:n])
    def test_bad_enums(self):
        for method,body,offset,value in ((9,STATE,8,51),(9,STATE,21,51),(9,STATE,30,9),(10,DESC,22,2),(10,DESC,23,2),(10,DESC,28,2),(10,DESC,33,59)):
            b=bytearray(body);b[offset]=value
            with self.subTest(offset=offset),self.assertRaises(ValueError):decode_graph_body(method,bytes(b))
    def test_array_extent_is_bytes(self):
        b=bytearray(DESC);b[50:54]=struct.pack('>I',1)
        with self.assertRaises(ValueError):decode_graph_body(10,bytes(b))
    def test_payload_extent(self):
        for method,b in ((9,STATE),(10,DESC)):
            with self.assertRaises(ValueError):decode_graph_body(method,b+b'\0')
            bad=b[:9]+struct.pack('>I',0xffffffff)+b[13:]
            with self.assertRaises(ValueError):decode_graph_body(method,bad)
    def test_identity_mismatch(self):
        b=bytearray(STATE);b[20]^=1
        self.assertFalse(decode_graph_body(9,bytes(b))['list_state']['outer_identity_matches'])
    def test_unknown_and_empty(self):
        self.assertNotIn('list_state',decode_graph_body(9,STATE[:13]+struct.pack('>I',99)+STATE[17:]))
        with self.assertRaises(ValueError):decode_graph_body(9,STATE[:13]+b'\0'*4+STATE[17:])
        self.assertEqual(decode_graph_body(9,STATE[:9]+b'\0'*8)['payload_bytes'],0)
    def test_nonfinite_preserved_as_bits(self):
        b=STATE[:47]+bytes.fromhex('7ff0000000000000')+STATE[55:]
        r=decode_graph_body(9,b)['list_state']
        self.assertIsNone(r['route_length']);self.assertEqual(r['route_length_bits'],'7ff0000000000000')
    def test_negative_sentinel_is_not_normalized(self):
        b=STATE[:47]+struct.pack('>d',-sys.float_info.max)+STATE[55:]
        self.assertEqual(decode_graph_body(9,b)['list_state']['route_length'],-sys.float_info.max)
    def test_packet_envelope(self):
        p=struct.pack('>HHIHHBBBB',0xb006,9,len(STATE)+8,1,2,1,1,0,0)+STATE
        self.assertEqual(decode_graph_packet(p)['client'],1)
        for offset in (0,3,7,12,13,14,15):
            b=bytearray(p);b[offset]^=2
            with self.subTest(offset=offset),self.assertRaises(ValueError):decode_graph_packet(bytes(b))
    def test_state_transition_table(self):
        expected=[{0,1},{1,2,4,5,8},{2,3,4,5,6,7,8},{1,3},{2,3,4,5,6,7,8},{0,1,5},{0,6},{2,4,5,7,8},{2,3,4,5,6,7,8}]
        for previous in range(9):
            self.assertEqual({n for n in range(9) if factory_state_transition_allowed(previous,n)},expected[previous])
        with self.assertRaises(ValueError):factory_state_transition_allowed(9,0)
    def test_independent_visibility_not_inferred(self):
        r=decode_graph_body(9,STATE)
        self.assertFalse(r['live_drawing_allowed']);self.assertFalse(r['remote_cleanup_proven'])
