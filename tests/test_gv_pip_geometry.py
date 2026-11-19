import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_gv_pip_geometry import decode

def packet(w,h,sequence=0xfffffffe):
    return struct.pack('<IIIII',0x80000000,0,sequence,0x70008,12)+struct.pack('<BBHHBBI',0,2,w,h,0,1,2)
class Geometry(unittest.TestCase):
    def test_retained_native_geometry_not_rescaled_or_marked_live(self):
        for size in [(800,480),(480,431),(0,0)]:
            r=decode(packet(*size));self.assertEqual((r['width'],r['height']),size)
            self.assertEqual((r['depth'],r['packing'],r['picture_id']),(0,1,2))
            self.assertTrue(r['reusable']);self.assertFalse(r['active_frame_proven']);self.assertFalse(r['windshield_destination_proven'])
    def test_sequence_alone_does_not_prove_active_frame(self):
        r=decode(packet(800,480,7));self.assertFalse(r['reusable']);self.assertFalse(r['active_frame_proven'])
    def test_trailing_previous_commands_not_interpreted(self):
        r=decode(packet(800,480)+packet(460,237));self.assertEqual(r['width'],800)
    def test_truncated_and_extended_payload_rejected(self):
        b=packet(800,480)
        for n in range(len(b)):
            with self.assertRaises(ValueError):decode(b[:n])
        c=bytearray(b+bytes(4));struct.pack_into('<I',c,16,16)
        with self.assertRaises(ValueError):decode(bytes(c))
    def test_other_first_chunk_not_scanned_for_embedded_pip(self):
        p=struct.pack('<IIIII',0,0,0xfffffffe,1,0)+packet(800,480)
        self.assertIsNone(decode(p))
if __name__=='__main__':unittest.main()
