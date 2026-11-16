import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_resource import decode_resource_body, decode_resource_packet, encode_bitmap_body

# Synthetic fixed byte vector, not an observed or accepted vehicle message.
VECTOR=bytes.fromhex('01020304 11223344 02 00000010 00000002 11223344 02 0010 0020 00000003 aabbcc')

class ResourceTests(unittest.TestCase):
    def test_fixed_vector_encoding(self):
        self.assertEqual(encode_bitmap_body(0x01020304,0x11223344,2,[16,32],b'\xaa\xbb\xcc'),VECTOR)

    def test_fixed_vector_decoding(self):
        r=decode_resource_body(VECTOR)
        self.assertEqual(r['bitmap']['resolution_pair'],[16,32])
        self.assertEqual(r['bitmap']['image_bytes'],3)
        self.assertTrue(r['bitmap']['outer_identity_matches'])
        self.assertFalse(r['live_drawing_allowed'])
        self.assertFalse(r['resource_ownership_proven'])

    def test_every_truncation_rejected(self):
        for n in range(len(VECTOR)):
            with self.assertRaises(ValueError):decode_resource_body(VECTOR[:n])

    def test_trailing_rejected(self):
        with self.assertRaises(ValueError):decode_resource_body(VECTOR+b'\0')

    def test_outer_type_rejected(self):
        b=bytearray(VECTOR);b[8]=12
        with self.assertRaises(ValueError):decode_resource_body(bytes(b))

    def test_inner_type_rejected(self):
        b=bytearray(VECTOR);b[21]=12
        with self.assertRaises(ValueError):decode_resource_body(bytes(b))

    def test_inner_identity_mismatch_is_evidence(self):
        b=bytearray(VECTOR);b[17]^=1
        self.assertFalse(decode_resource_body(bytes(b))['bitmap']['outer_identity_matches'])

    def test_variant_and_image_extent_rejected(self):
        for offset in (9,26):
            b=bytearray(VECTOR);b[offset:offset+4]=struct.pack('>I',999)
            with self.assertRaises(ValueError):decode_resource_body(bytes(b))

    def test_unknown_variant_opaque(self):
        b=bytearray(VECTOR);b[13:17]=struct.pack('>I',99)
        self.assertNotIn('bitmap',decode_resource_body(bytes(b)))

    def test_empty_variant_rejected_with_payload(self):
        b=bytearray(VECTOR);b[13:17]=bytes(4)
        with self.assertRaises(ValueError):decode_resource_body(bytes(b))

    def test_packet_envelope(self):
        p=struct.pack('>HHIHHBBBB',0xb006,3,len(VECTOR)+8,13,42,1,1,0,0)+VECTOR
        self.assertEqual(decode_resource_packet(p)['session'],42)
        for offset in (0,3,7,12,13,14,15):
            b=bytearray(p);b[offset]^=1
            with self.assertRaises(ValueError):decode_resource_packet(bytes(b))

    def test_encoding_bounds(self):
        cases=[(-1,1,1,[1,1],b''),(1,True,1,[1,1],b''),(1,1,12,[1,1],b''),
               (1,1,1,[1],b''),(1,1,1,[65536,1],b''),(1,1,1,[1,1],b'\0'*65536)]
        for args in cases:
            with self.assertRaises(ValueError):encode_bitmap_body(*args)
