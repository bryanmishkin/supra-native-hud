import json,struct,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class SinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.binary=str(Path(cls.tmp.name)/'inspect')
        subprocess.run(['c++','-std=c++98','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(ROOT/'src/someip_model.cpp'),str(ROOT/'tools/hud_model_inspect.cpp'),'-o',cls.binary],check=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def decode(self,body,method=0x8001,kind=2,version=1,rc=0,service=0xb009):
        b=struct.pack('>HHIHHBBBB',service,method,len(body)+8,0,1,1,version,kind,rc)+body
        r=subprocess.run([self.binary],input=b,capture_output=True,timeout=3);self.assertEqual(r.returncode,0);return json.loads(r.stdout)
    def test_event_raw_fields(self):
        r=self.decode(struct.pack('>IIHHB',0x12345678,0x90abcdef,0x1234,0xabcd,7))
        self.assertTrue(r['sink_decoded']);self.assertEqual(r['sink_first_high'],0x12345678);self.assertEqual(r['sink_first_low'],0x90abcdef)
        self.assertEqual(r['sink_pair'],[0x1234,0xabcd]);self.assertEqual(r['sink_final'],7);self.assertFalse(r['drawing_authorized']);self.assertFalse(r['decoded'])
    def test_completion_raw_fields(self):
        r=self.decode(bytes([7,9]),1,1);self.assertTrue(r['sink_decoded']);self.assertEqual(r['sink_completion'],[7,9])
    def test_exact_lengths(self):
        for n in list(range(13))+[14,100]:self.assertFalse(self.decode(bytes(n))['sink_decoded'])
        for n in [0,1,3,13]:self.assertFalse(self.decode(bytes(n),1,1)['sink_decoded'])
    def test_wrong_envelope(self):
        for kw in [dict(kind=0),dict(kind=128),dict(version=2),dict(rc=1),dict(service=0xb006),dict(method=1)]:
            self.assertFalse(self.decode(bytes(13),**kw)['sink_decoded'])
if __name__=='__main__':unittest.main()
