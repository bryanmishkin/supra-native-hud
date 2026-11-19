import importlib.util,pathlib,unittest,tempfile,struct
spec=importlib.util.spec_from_file_location('marker',pathlib.Path(__file__).parents[1]/'tools'/'canvas_pip320_marker.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MarkerTests(unittest.TestCase):
 def test_card(self):
  b=m.marker();self.assertEqual(len(b),320*320*4)
  self.assertEqual(b[3::4],bytes([255])*(320*320))
  self.assertEqual(b[(20*320+20)*4:(20*320+20)*4+4],bytes([0,0,255,255]))
  self.assertTrue(m.png(b).startswith(b'\x89PNG\r\n\x1a\n'))
 def test_output(self):
  with tempfile.TemporaryDirectory() as d:
   path=pathlib.Path(d)/'card';self.assertEqual(m.main(['--output',str(path)]),0)
   self.assertTrue((path/'pip320-marker.bgra').is_file())
   with self.assertRaises(SystemExit):m.main(['--output',str(path)])
if __name__=='__main__':unittest.main()

