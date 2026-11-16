import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
from audit_model_sessions import audit

def frame(kind=0,rc=0,method=4,svc=0xb00e):
    b=bytes([0,0,0,7]) if kind==0 else b''
    return struct.pack('>HHIHHBBBB',svc,method,len(b)+8,1,2,1,1,kind,rc)+b
F=['a',100,'b',200];R=['b',200,'a',100]
class SessionTests(unittest.TestCase):
    def test_pair_and_no_ownership_inference(self):
        r=audit([(F,frame()),(R,frame(128))]);self.assertEqual(r['transactions'][0]['status'],'ok');self.assertFalse(r['independently_owned_surface_proven'])
    def test_other_connection_reply_does_not_match(self):
        r=audit([(F,frame()),(['b',200,'a',101],frame(128))])
        self.assertEqual(sorted(x['status'] for x in r['transactions']),['missing_reply','missing_request'])
    def test_repeated_identifiers_are_ambiguous(self):
        r=audit([(F,frame()*2),(R,frame(128)*2)]);self.assertEqual(r['transactions'][0]['status'],'ambiguous')
    def test_rejection_and_candidate_are_not_allocation(self):
        r=audit([(F,frame(method=1)),(R,frame(129,1,method=1))]);self.assertEqual(r['transactions'][0]['status'],'rejected');self.assertEqual(len(r['method_1_candidates']),1);self.assertFalse(r['independently_owned_surface_proven'])
    def test_handle_namespace_includes_service(self):
        r=audit([(F,frame()+frame(method=9,svc=0xb006))]);self.assertEqual(len(r['observed_factory_handle_prefixes']),2)
    def test_invalid_framing_rejected(self):
        with self.assertRaises(ValueError):audit([(F,frame()[:-1])])
if __name__=='__main__':unittest.main()
