import json,struct,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class InspectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.binary=str(Path(cls.tmp.name)/'inspect')
        subprocess.run(['c++','-std=c++98','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(ROOT/'src/someip_model.cpp'),str(ROOT/'tools/hud_model_inspect.cpp'),'-o',cls.binary],check=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def invoke(self,data):return subprocess.run([self.binary],input=data,capture_output=True,timeout=3)
    def frame(self,body,kind=0):return struct.pack('>HHIHHBBBB',0xb00e,4,len(body)+8,1,1,1,1,kind,0)+body
    def test_request_and_response_separation(self):
        r=self.invoke(self.frame(bytes([0,0,0,7]))+self.frame(bytes([0,0,0,7]),128))
        self.assertEqual(r.returncode,0);rows=[json.loads(x) for x in r.stdout.splitlines()]
        self.assertTrue(rows[0]['decoded']);self.assertFalse(rows[1]['decoded']);self.assertFalse(rows[0]['drawing_authorized'])
    def test_every_truncation_fails(self):
        data=self.frame(bytes([0,0,0,7]))
        for i in range(1,len(data)):
            with self.subTest(i=i):self.assertEqual(self.invoke(data[:i]).returncode,2)
    def test_invalid_protocol_and_oversized_message(self):
        data=bytearray(self.frame(bytes(4)));data[12]=2
        self.assertEqual(self.invoke(data).returncode,2)
        data[12]=1;data[4:8]=struct.pack('>I',65545)
        self.assertEqual(self.invoke(data).returncode,2)
if __name__=='__main__':unittest.main()
