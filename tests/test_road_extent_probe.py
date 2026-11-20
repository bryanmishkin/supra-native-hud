import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from road_extent_probe import image
from ric_rle32 import encode_bgra,decode_bgra,swap_red_blue
class ExtentProbe(unittest.TestCase):
    def test_exact_sizes_and_far_edge_survive_encoding(self):
        for i,width in [(0,150),(1,64)]:
            w,h,raw=image(i)
            self.assertEqual((w,h,len(raw)),(width,36,width*36*4))
            encoded=encode_bgra(swap_red_blue(raw))
            self.assertEqual(decode_bgra(encoded,w*h),swap_red_blue(raw))
        w,h,raw=image(1)
        for y in range(h):
            for x in range(60,64):self.assertEqual(raw[(y*w+x)*4:(y*w+x+1)*4],bytes((0,255,0,255)))
    def test_no_third_slot(self):
        with self.assertRaises(ValueError):image(2)
if __name__=='__main__':unittest.main()
