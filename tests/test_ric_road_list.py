import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_road_list import decode,encode,two_image_candidates
CONTROL=bytes.fromhex('000000c827000004280000001500000002270000042800000000000a00000004010000080000')
class RoadListCodec(unittest.TestCase):
    def test_control_and_cleanup(self):
        v=decode(CONTROL);self.assertEqual(encode(v),CONTROL)
        candidates=two_image_candidates(CONTROL,0x01000008,0x01000009)
        self.assertEqual(decode(candidates['two_icons_one_entry'])['entries'],[dict(resources=[0x01000008,0x01000009],trailing_bytes=[0,0])])
        self.assertEqual(len(decode(candidates['one_icon_two_entries'])['entries']),2)
        self.assertEqual(candidates['withdraw'].hex(),'000000c827000004280000000b000000022700000428000000000000')
    def test_all_truncations_rejected(self):
        for n in range(len(CONTROL)):
            with self.subTest(n=n),self.assertRaises(ValueError):decode(CONTROL[:n])
        with self.assertRaises(ValueError):decode(CONTROL+b'\0')
    def test_identity_and_lengths(self):
        for offset in (8,12,16,20,21,27,31):
            b=bytearray(CONTROL);b[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(ValueError):decode(bytes(b))
    def test_limits_and_slot_separation(self):
        v=decode(CONTROL);v['entries']*=11
        with self.assertRaises(ValueError):encode(v)
        v=decode(CONTROL);v['entries'][0]['resources']*=11
        with self.assertRaises(ValueError):encode(v)
        for ids in [(0x01000008,0x01000008),(0x01000000,0x01000009)]:
            with self.assertRaises(ValueError):two_image_candidates(CONTROL,*ids)
if __name__=='__main__':unittest.main()
