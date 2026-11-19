import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from b00e_carousel import encode,decode,replace_selected_content
class ContentBindingTests(unittest.TestCase):
 def setUp(self):
  self.rows=[[0x0700002b,0x03000000,0x03000000,0xffffffff],[0x07000039,0x03000001,0x03000001,0xffffffff],[0x07000029,0x03000002,0x03000002,0xffffffff],[0x0700002d,0x03000003,0x03000003,0xffffffff]]
  self.body=encode(100,0x6d,0x1c,1,self.rows,b'\0\1\0')
 def test_only_selected_content_word_changes(self):
  for field in (1,2):
   candidate=replace_selected_content(self.body,0x01000009,field)
   expected=[row[:] for row in self.rows];expected[1][field]=0x01000009
   model=decode(candidate)
   self.assertEqual(model['elements'],expected)
   self.assertEqual(model['index'],1);self.assertEqual(model['trailing'],b'\0\1\0')
   # Wire offset: 17-byte envelope, 10-byte inner prefix, 16-byte rows.
   offset=27+16+field*4
   self.assertEqual(candidate[:offset],self.body[:offset])
   self.assertEqual(candidate[offset+4:],self.body[offset+4:])
   self.assertEqual(decode(self.body)['elements'],self.rows)
 def test_no_icon_or_unknown_field_substitution(self):
  for field in (0,3,-1,True):
   with self.assertRaises(ValueError):replace_selected_content(self.body,0x01000009,field)
 def test_invalid_selection_rejected(self):
  for rows,index in (([],0),(self.rows,4),(self.rows,255)):
   with self.assertRaises(ValueError):replace_selected_content(encode(100,0x6d,0x1c,index,rows,b'\0\1\0'),0x01000009,1)
 def test_wrong_model_rejected(self):
  with self.assertRaises(ValueError):replace_selected_content(encode(100,0x6e,0x2f,1,self.rows,b'\0\1\0'),0x01000009,1)
if __name__=='__main__':unittest.main()
