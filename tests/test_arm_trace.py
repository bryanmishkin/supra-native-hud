import sys,struct,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
from trace_arm_region import trace,read_virtual

def fixture(machine=40):
    ident=b'\x7fELF'+bytes([1,1,1])+bytes(9)
    header=ident+struct.pack('<HHIIIIIHHHHHH',2,machine,1,0x1000,52,0,0,52,32,1,40,0,0)
    ph=struct.pack('<IIIIIIII',1,256,0x1000,0x1000,256,512,5,4)
    segment=bytearray(256);struct.pack_into('<III',segment,0,0xe59f0000,0xe12fff1e,0x1020);segment[32:42]=b'testlabel\0'
    return header+ph+bytes(256-len(header)-len(ph))+segment
class TraceTests(unittest.TestCase):
    def with_file(self,data,**kwargs):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fixture';p.write_bytes(data);return trace(p,**kwargs)
    def test_literal_mapping_and_string(self):
        r=self.with_file(fixture(),address=0x1000,size=4)
        self.assertEqual(r['rows'][0]['pc_relative_word'],'0x1020');self.assertEqual(r['rows'][0]['possible_string'],'testlabel')
    def test_word_mode_does_not_claim_instructions(self):
        r=self.with_file(fixture(),address=0x1008,size=4,words=True)
        self.assertEqual(r['mode'],'words');self.assertEqual(r['rows'][0]['value'],'0x1020')
    def test_file_backed_bounds_and_alignment(self):
        for addr,size in [(0x1100,4),(0x1001,4),(0x1000,3),(0x1000,20000)]:
            with self.assertRaises(ValueError):self.with_file(fixture(),address=addr,size=size)
        with self.assertRaises(ValueError):read_virtual(b'a',[(0,0,1)],0,2)
    def test_wrong_architecture(self):
        with self.assertRaises(ValueError):self.with_file(fixture(3),address=0x1000,size=4)
if __name__=='__main__':unittest.main()
