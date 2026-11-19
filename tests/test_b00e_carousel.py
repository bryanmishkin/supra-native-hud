import sys,unittest,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from b00e_carousel import encode,decode
from b00e_resource_lifecycle import check_body,check_reply,dispose_resource_body,dispose_reply

# Synthetic IDs. Layout follows the separately replayed private voice captures.
V=bytes.fromhex('01020304 11121314 2f 0000001d 0000000a 11121314 2f 00 00000010 0700005b 0300002c 0300002c ffffffff 000000')
class B00ETests(unittest.TestCase):
    def test_fixed_wire_layout(self):
        x=decode(V);self.assertEqual(x['elements'][0],[0x0700005b,0x0300002c,0x0300002c,0xffffffff]);self.assertEqual(encode(**x),V)
    def test_truncation_and_trailing(self):
        for n in range(len(V)):
            with self.assertRaises(ValueError):decode(V[:n])
        with self.assertRaises(ValueError):decode(V+b'\0')
    def test_inconsistent_identity_and_lengths(self):
        for offset in [17,21,26]:
            b=bytearray(V);b[offset]^=1
            with self.assertRaises(ValueError):decode(bytes(b))
    def test_variant_not_interchangeable(self):
        b=bytearray(V);b[16]=8
        with self.assertRaises(ValueError):decode(bytes(b))
    def test_resource_reply_errors_not_presence(self):
        for body in [b'',b'\2',b'\1\0']:
            with self.assertRaises(ValueError):check_reply(body)
        with self.assertRaises(ValueError):check_reply(b'\0',return_code=1)
        self.assertFalse(check_reply(b'\0'));self.assertTrue(check_reply(b'\1'))
    def test_disposal_not_removal_proof(self):
        self.assertFalse(dispose_reply(b'')['resource_absent_verified'])
        with self.assertRaises(ValueError):dispose_reply(b'\0')
        self.assertEqual(check_body(1,2,1),struct.pack('>IIB',1,2,1))
        self.assertEqual(dispose_resource_body(1,2),struct.pack('>II',1,2))
    def test_bounded_builder(self):
        x=decode(V);x['elements']*=5
        with self.assertRaises(ValueError):encode(**x)
        x=decode(V);x['handle']=True
        with self.assertRaises(ValueError):encode(**x)
if __name__=='__main__':unittest.main()
