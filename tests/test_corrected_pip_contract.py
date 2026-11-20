import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_corrected_pip_trial import producer_contract,validate_producer
class ContractTests(unittest.TestCase):
    def setUp(self):
        self.a={'models':{15:0x0f000004},'resource_id':0x02000004,'style':'day'}
    def test_requires_actual_sink_confirmation(self):
        raw=b'PIP_BINDING '+json.dumps(producer_contract(self.a)).encode()+b'\n'
        with self.assertRaises(ValueError):validate_producer(raw,self.a)
        validate_producer(b'SINK_NEGOTIATED_CLUSTER\n'+raw,self.a)
    def test_rejects_old_dimensions_and_nonhud_flag(self):
        for key,value in [('content',[320,200]),('destination_flag',1),('selection',0),('style','night')]:
            row=producer_contract(self.a);row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_producer(b'SINK_NEGOTIATED_CLUSTER\nPIP_BINDING '+json.dumps(row).encode(),self.a)
    def test_candidate_requires_matching_hud_confirmation(self):
        self.a['allow_hud_candidate']=True
        row=producer_contract(self.a);row['selection']=0
        line=b'PIP_BINDING '+json.dumps(row).encode()+b'\n'
        validate_producer(b'SINK_NEGOTIATED_HUD_CANDIDATE\n'+line,self.a)
        with self.assertRaises(ValueError):validate_producer(b'SINK_NEGOTIATED_CLUSTER\n'+line,self.a)
    def test_default_rejects_candidate_schema(self):
        row=producer_contract(self.a);row['schema']=4
        with self.assertRaises(ValueError):validate_producer(b'SINK_NEGOTIATED_CLUSTER\nPIP_BINDING '+json.dumps(row).encode(),self.a)
    def test_rejects_duplicate_contract(self):
        line=b'PIP_BINDING '+json.dumps(producer_contract(self.a)).encode()+b'\n'
        with self.assertRaises(ValueError):validate_producer(b'SINK_NEGOTIATED_CLUSTER\n'+line+line,self.a)
if __name__=='__main__':unittest.main()
