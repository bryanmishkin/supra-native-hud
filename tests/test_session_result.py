import importlib.util
import json
from pathlib import Path
import unittest
s=importlib.util.spec_from_file_location('check_result',Path(__file__).parents[1]/'tools/check_session_result.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class ResultsTest(unittest.TestCase):
    def registry(self):
        return dict(schema=2,hud_commands_sent=0,payloads_captured=False,dropped_snapshots=0,dropped_headers=0,bad_messages=0,link_state='up',self_address=0x2001,elapsed_ms=15000,snapshots=[[dict(key=0x8200,address=0x101)]],headers=[])
    def check(self,r,code=0):return m.analyze('[DSI] diagnostic log\n'+json.dumps(r),'registry',code)
    def test_valid_registry(self):
        r=self.check(self.registry());self.assertTrue(r['evidence_usable']);self.assertFalse(r['drawing_authorized'])
    def test_missing_and_conflicting_hosts(self):
        for snapshots in [[[]],[[dict(key=0x8200,address=0x101),dict(key=0x8200,address=0x102)]],[[dict(key=0x8200,address=0x101)],[dict(key=0x8200,address=0x102)]]]:
            r=self.registry();r['snapshots']=snapshots;self.assertFalse(self.check(r)['evidence_usable'])
    def test_failed_or_incomplete_capture(self):
        for key,value in [('hud_commands_sent',1),('dropped_headers',1),('elapsed_ms',1000),('link_state','detached'),('bad_messages',1)]:
            r=self.registry();r[key]=value;self.assertFalse(self.check(r)['evidence_usable'])
        self.assertFalse(self.check(self.registry(),124)['evidence_usable'])
    def test_truncated_and_duplicate_json(self):
        for text in ['{"schema":2',json.dumps(self.registry())+'\n'+json.dumps(self.registry())]:
            with self.assertRaises(ValueError):m.analyze(text,'registry',0)
    def test_selftest_requires_target_and_complete_suite(self):
        r=dict(schema=1,qnx_target=True,pointer_bits=32,vehicle_io=False,tests=[dict(name=n,pass_=True) for n in []],pass_=True)
        r['pass']=True;r['tests']=[{'name':n,'pass':True} for n in m.EXPECTED_TESTS]
        self.assertTrue(m.analyze(json.dumps(r),'selftest',0)['evidence_usable'])
        r['qnx_target']=False;self.assertFalse(m.analyze(json.dumps(r),'selftest',0)['evidence_usable'])
        r['qnx_target']=True;r['tests'].pop();self.assertFalse(m.analyze(json.dumps(r),'selftest',0)['evidence_usable'])
if __name__=='__main__':unittest.main()
