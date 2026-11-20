import pathlib,sys,struct,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from b006_ccp_position import encode,decode,without_picture,ABSENT
class Position(unittest.TestCase):
 def test_native_payload_vector(self):
  b=encode(200,0x1e000001,[138,80],0x01000008,90)
  self.assertEqual(b[17:].hex(),'1e0000011e008a005001000008005a')
  self.assertEqual(decode(b)['center'],[138,80]);self.assertFalse(decode(b)['live_admission_proven'])
 def test_reference_withdrawal_preserves_other_fields(self):
  b=encode(200,0x1e000001,[138,80],0x01000009,0);c=without_picture(b)
  self.assertEqual(c[:26],b[:26]);self.assertEqual(c[30:],b[30:]);self.assertEqual(decode(c)['picture_resource_id'],ABSENT)
 def test_reject_identity_and_extents(self):
  b=encode(200,0x1e000001,[0,0],ABSENT,0)
  for x in(b[:-1],b+b'\0',b[:17]+b'\0\0\0\0'+b[21:]):
   with self.assertRaises(ValueError):decode(x)
  with self.assertRaises(ValueError):encode(200,0x1e000001,[65536,0],ABSENT,0)
if __name__=='__main__':unittest.main()
