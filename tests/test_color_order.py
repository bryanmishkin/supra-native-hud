import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_rle32 import swap_red_blue,encode_bgra,decode_bgra
class ColorOrder(unittest.TestCase):
 def test_mapping_and_alpha(self):
  raw=bytes((0,150,255,255,0,40,255,255,255,255,255,255,0,0,0,255))
  corrected=bytes((255,150,0,255,255,40,0,255,255,255,255,255,0,0,0,255))
  self.assertEqual(swap_red_blue(raw),corrected)
  self.assertEqual(swap_red_blue(corrected),raw)
  self.assertEqual(decode_bgra(encode_bgra(corrected),4),corrected)
 def test_invalid(self):
  for raw in (b'',b'abc',bytearray(4)):
   with self.assertRaises(ValueError):swap_red_blue(raw)
