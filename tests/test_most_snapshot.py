import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from capture_most_snapshot import assess
class Tests(unittest.TestCase):
    def data(self,**changes):
        d=dict(schema=2,all_headers=True,hud_commands_sent=0,payloads_captured=False,link_state='up',snapshots=[[{'address':20480,'key':1280}]],dropped_snapshots=0,dropped_headers=0,bad_messages=0,elapsed_ms=15001)
        d.update(changes);return json.dumps(d).encode()
    def test_valid_scope(self):self.assertEqual(assess(self.data())['hud_commands_sent'],0)
    def test_missing_drops_not_assumed_zero(self):
        d=json.loads(self.data());del d['dropped_headers']
        with self.assertRaises(ValueError):assess(json.dumps(d).encode())
    def test_refuses_send_loss_and_no_registry(self):
        for change in ({'hud_commands_sent':1},{'dropped_headers':1},{'snapshots':[]},{'link_state':'refused'},{'elapsed_ms':22000}):
            with self.assertRaises(ValueError):assess(self.data(**change))
if __name__=='__main__':unittest.main()
