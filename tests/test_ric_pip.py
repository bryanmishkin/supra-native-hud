import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_resource import decode_resource_body

# Independent synthetic descriptor; not a captured vehicle acceptance.
V=bytes.fromhex('01020304 02000001 02 0000000b 00000003 02000001 02 0010 0020 01 00')
class PipTests(unittest.TestCase):
    def test_descriptor(self):
        r=decode_resource_body(V)
        p=r['picture_in_picture']
        self.assertEqual(p['resolution_pair'],[16,32])
        self.assertTrue(p['outer_identity_matches'])
        self.assertFalse(p['pixel_payload_present'])
        self.assertFalse(r['live_drawing_allowed'])
    def test_truncations(self):
        for n in range(len(V)):
            with self.assertRaises(ValueError):decode_resource_body(V[:n])
    def test_appended_image_rejected(self):
        b=bytearray(V+b'pixels'); b[9:13]=(17).to_bytes(4,'big')
        with self.assertRaises(ValueError):decode_resource_body(bytes(b))
    def test_enum_bounds(self):
        for offset,value in [(21,12),(26,2),(27,3)]:
            b=bytearray(V);b[offset]=value
            with self.assertRaises(ValueError):decode_resource_body(bytes(b))
    def test_mismatch(self):
        b=bytearray(V);b[20]^=1
        self.assertFalse(decode_resource_body(bytes(b))['picture_in_picture']['outer_identity_matches'])
