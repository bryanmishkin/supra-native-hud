import pathlib,sys,unittest,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from b006_distance import decode,encode,replace_distance
BODY=bytes.fromhex('000000c81d00001d1d00000028000000041d00001d1dff407cd0000000000000000005214364646400000004feff0000030000000000010edd')
class Distance(unittest.TestCase):
 def test_exact_saved_shape(self):
  d=decode(BODY);self.assertEqual(d['distance'],461);self.assertEqual(d['unit'],3);self.assertEqual(encode(d),BODY)
 def test_numeric_field_only(self):
  for n in(461,3000,92,91,70,69,0):
   b=replace_distance(BODY,n);self.assertEqual(decode(b)['distance'],n);self.assertEqual(b[:23],BODY[:23]);self.assertEqual(b[31:],BODY[31:])
 def test_reject_bad_shapes_and_nonfinite(self):
  for b in(BODY[:-1],BODY+b'\0',BODY[:31]+b'\xff'*4+BODY[35:]):
   with self.assertRaises(ValueError):decode(b)
  for n in(-1,10001,float('nan'),float('inf'),True):
   with self.assertRaises(ValueError):replace_distance(BODY,n)
if __name__=='__main__':unittest.main()
