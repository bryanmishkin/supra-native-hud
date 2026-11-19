import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from canvas_geometry import SIZES,ruler,validate_size
from ric_rle32 import encode_bgra,decode_bgra
from run_canvas_case import command
from prepare_canvas_binding_tests import build
from b00e_carousel import encode

class GeometryTests(unittest.TestCase):
 def test_edges_aspect_and_roundtrip(self):
  for w,h in SIZES:
   b=ruler(w,h)
   self.assertEqual(len(b),w*h*4)
   self.assertEqual(decode_bgra(encode_bgra(b),w*h),b)
   def at(x,y):return tuple(b[4*(y*w+x):4*(y*w+x)+4])
   self.assertEqual(at(w//2,0),(255,255,0,255))
   self.assertEqual(at(w//2,h-1),(0,128,255,255))
   self.assertEqual(at(0,h//2),(0,255,0,255))
   self.assertEqual(at(w-1,h//2),(255,0,255,255))
 def test_bounds(self):
  for size in [(129,128),(128,129),(0,0),(True,36),(320,320)]:
   with self.assertRaises(ValueError):validate_size(*size)
 def test_generated_rectangle_dispatched_without_square_coercion(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);snap=root/'snapshot.bin'
   snap.write_bytes(encode(100,0x6d,0x1c,0,[[0x07000029,0x03000000,0xffffffff,0xffffffff]],b'\0\1\0'))
   kit=root/'kit';m=build(snap,kit)
   self.assertEqual(len(m['cases']),30)
   args=command(kit,'content-1-128x36-ruler',1234,root/'admission',root/'result')
   self.assertEqual(args[args.index('--width')+1],'128')
   self.assertEqual(args[args.index('--height')+1],'36')
   self.assertNotIn('--size',args)
   asset=kit/'content-1-128x36-ruler.bgra';asset.write_bytes(b'bad')
   with self.assertRaises(ValueError):command(kit,'content-1-128x36-ruler',1234,root/'admission',root/'result')
if __name__=='__main__':unittest.main()
