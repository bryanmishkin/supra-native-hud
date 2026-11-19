import importlib.util, pathlib, struct, unittest
PATH=pathlib.Path(__file__).parents[1]/'tools'/'canvas_resource_presence.py'
spec=importlib.util.spec_from_file_location('presence',PATH)
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

def profile():
    pip=struct.pack('>BBIIHHBB',35,2,5,p.RANGE_START,320,320,1,0)
    v=struct.pack('>II',len(pip),35)+pip
    body=struct.pack('>II',200,len(v))+v
    return struct.pack('>HHIHHBBBB',0xb006,1,len(body)+8,5,1,1,1,0x80,0)+body
class Tests(unittest.TestCase):
    def test_decode(self):
        o=p.decode_known_profile(profile());self.assertEqual(o['pip']['max_resolution'],[320,320])
        with self.assertRaises(ValueError):p.decode_known_profile(profile()[:-1])
        with self.assertRaises(ValueError):p.decode_known_profile(profile().replace(b'\x01\x40',b'\x01\x41'))
    def test_read_only_sequence(self):
        calls=[]
        def fake(req,timeout):
            calls.append(req)
            svc,m,n,c,s,_,_,_,_=struct.unpack_from('>HHIHHBBBB',req)
            self.assertEqual((svc,m,n,timeout),(0xb006,2,17,2))
            v=(s==3)
            return struct.pack('>HHIHHBBBBB',svc,m,9,c,s,1,1,0x80,0,int(v))
        result=p.probe(profile(),fake)
        self.assertEqual(len(result['results']),5)
        self.assertEqual(sum(x['present'] for x in result['results']),1)
        self.assertTrue(all(req[16:20]==b'\x00\x00\x00\xc8' for req in calls))
        self.assertFalse(result['draw_attempted']);self.assertFalse(result['exclusive_ownership_proven'])
    def test_reject_wrong_reply(self):
        req=p.check_packet(p.RANGE_START,1)
        bad=struct.pack('>HHIHHBBBBB',0xb006,2,9,0x5350,2,1,1,0x80,0,0)
        with self.assertRaises(ValueError):p.verify_reply(req,bad)
    def test_invalid_slot(self):
        with self.assertRaises(ValueError):p.check_packet(0x01000009,1)
    def test_default_dry_run(self): self.assertEqual(p.main([]),0)
if __name__=='__main__':unittest.main()

