import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from road_boundary_ruler import tile
class BoundaryPixels(unittest.TestCase):
    def test_distinct_edges_and_exact_extent(self):
        a,b=tile(0),tile(1)
        self.assertEqual(len(a),150*36*4)
        self.assertEqual(len(b),len(a))
        def pixel(raw,x,y):return raw[4*(150*y+x):4*(150*y+x+1)]
        self.assertEqual(pixel(a,0,18),bytes((255,200,0,255)))
        self.assertEqual(pixel(b,149,18),bytes((0,255,0,255)))
        self.assertEqual(pixel(a,149,18),pixel(b,0,18))
        self.assertNotEqual(a,b)
if __name__=='__main__':unittest.main()
