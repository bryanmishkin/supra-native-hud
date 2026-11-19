import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from catalog_guidance_styles import pair,catalog,FormatError
class CatalogTests(unittest.TestCase):
 def test_signed_coordinate_pairs(self):
  self.assertEqual(pair(0xffff8000),[-32768,-1])
  self.assertEqual(pair(31458080),[800,480])
 def test_hash_mismatch_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'file.hpp').write_bytes(b'changed')
   (root/'manifest.json').write_text(json.dumps({'files':{'/api/file.hpp':{'status':'verified','file':'file.hpp','bytes':7,'sha256':hashlib.sha256(b'correct').hexdigest()}}}))
   with self.assertRaises(FormatError):catalog(root)
 def test_capture_escape_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'manifest.json').write_text(json.dumps({'files':{'/api/file.hpp':{'status':'verified','file':'../outside','bytes':0,'sha256':''}}}))
   with self.assertRaises(FormatError):catalog(root)
if __name__=='__main__':unittest.main()
