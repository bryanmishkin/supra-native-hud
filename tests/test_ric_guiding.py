import struct
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from ric_guiding import decode_guiding_body, decode_guiding_packet, encode_high_roundabout_body

# Explicit synthetic IDs. Fixed vector independently states field widths/order.
VECTOR = bytes.fromhex('01020304 11121314 05 0000000b 00000007 11121314 05 03 02 21222324')

class GuidingTests(unittest.TestCase):
    def test_fixed_vector(self):
        self.assertEqual(encode_high_roundabout_body(0x01020304, 0x11121314, 5, 3, 2, 0x21222324), VECTOR)
        r = decode_guiding_body(VECTOR)
        self.assertEqual(r['high_roundabout']['picture_resource_id'], 0x21222324)
        self.assertTrue(r['high_roundabout']['outer_identity_matches'])
        self.assertFalse(r['live_drawing_allowed'])
    def test_every_truncation(self):
        for n in range(len(VECTOR)):
            with self.subTest(n=n), self.assertRaises(ValueError): decode_guiding_body(VECTOR[:n])
    def test_extent_and_trailing(self):
        for v in (VECTOR+b'\0', VECTOR[:9]+struct.pack('>I',10)+VECTOR[13:], VECTOR[:9]+struct.pack('>I',12)+VECTOR[13:]):
            with self.assertRaises(ValueError): decode_guiding_body(v)
    def test_enums(self):
        for offset, value in ((8,51),(21,51),(22,6),(23,0),(23,3)):
            v=bytearray(VECTOR);v[offset]=value
            with self.subTest(offset=offset,value=value), self.assertRaises(ValueError): decode_guiding_body(bytes(v))
    def test_identity_mismatch_is_reported(self):
        v=bytearray(VECTOR);v[20]^=1
        self.assertFalse(decode_guiding_body(bytes(v))['high_roundabout']['outer_identity_matches'])
    def test_unknown_variant_opaque(self):
        v=VECTOR[:13]+struct.pack('>I',99)+VECTOR[17:]
        self.assertNotIn('high_roundabout',decode_guiding_body(v))
    def test_zero_variant(self):
        with self.assertRaises(ValueError):decode_guiding_body(VECTOR[:13]+b'\0'*4+VECTOR[17:])
        self.assertEqual(decode_guiding_body(VECTOR[:9]+b'\0'*8)['payload_bytes'],0)
    def test_packet(self):
        p=struct.pack('>HHIHHBBBB',0xb006,11,len(VECTOR)+8,1,2,1,1,0,0)+VECTOR
        self.assertEqual(decode_guiding_packet(p)['session'],2)
        for off in (0,3,7,12,13,14,15):
            v=bytearray(p);v[off]^=1
            with self.subTest(offset=off), self.assertRaises(ValueError):decode_guiding_packet(bytes(v))
    def test_encoder_bounds(self):
        values=[1,2,3,4,1,5]
        for index,bad in ((0,-1),(1,2**32),(2,51),(3,6),(4,0),(5,True)):
            v=values.copy();v[index]=bad
            with self.assertRaises(ValueError):encode_high_roundabout_body(*v)
