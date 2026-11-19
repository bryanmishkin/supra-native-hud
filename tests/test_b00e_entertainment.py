import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from b00e_entertainment import encode,decode,replace_content_cell

class EntertainmentCodecTests(unittest.TestCase):
    def setUp(self):
        self.model=dict(handle=100,model_id=0x66,model_type=0x16,metadata=[0,0,2,5,2,5],header_reference=0x07000012,
            rows=[[[0xffffffff,1],[0x03000001,1],[0x03000002,1],[0x03000003,1],[0xffffffff,1]],
                  [[0xffffffff,1],[0x03000004,1],[0x03000005,1],[0x03000006,1],[0xffffffff,1]]],
            trailing_references=[0x0a000000,0x03000007,0x70,0x71])
        self.body=encode(**self.model)
    def test_roundtrip(self):self.assertEqual(decode(self.body),self.model)
    def test_only_resource_changes(self):
        changed=replace_content_cell(self.body,0x01000009,1,2)
        expected=decode(self.body);expected['rows'][1][2][0]=0x01000009
        self.assertEqual(decode(changed),expected)
        diffs=[i for i,(a,b) in enumerate(zip(self.body,changed)) if a!=b]
        self.assertLessEqual(len(diffs),4);self.assertLess(max(diffs)-min(diffs),4)
    def test_bad_identity(self):
        b=bytearray(self.body);b[20]^=1
        with self.assertRaises(ValueError):decode(bytes(b))
    def test_truncation_and_trailing(self):
        for b in [self.body[:-1],self.body+b'\0']:
            with self.assertRaises(ValueError):decode(b)
    def test_bad_variant(self):
        b=bytearray(self.body);b[16]=8
        with self.assertRaises(ValueError):decode(bytes(b))
    def test_row_and_column_bounds(self):
        for row,col in [(-1,1),(2,1),(0,0),(0,5),(True,1),(0,True)]:
            with self.assertRaises(ValueError):replace_content_cell(self.body,0x01000009,row,col)
    def test_bad_row_length(self):
        b=bytearray(self.body);b[42:46]=struct.pack('>I',24)
        with self.assertRaises(ValueError):decode(bytes(b))
    def test_absent_id_rejected(self):
        with self.assertRaises(ValueError):replace_content_cell(self.body,0xffffffff,0,1)
    def test_wrong_factory_snapshot(self):
        m=dict(self.model,model_id=0x68)
        with self.assertRaises(ValueError):replace_content_cell(encode(**m),0x01000009,0,1)

if __name__=='__main__':unittest.main()
