import json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from manage_road_list_session import Session,audit,CASES
class BatchGates(unittest.TestCase):
    def test_missing_control_blocks_before_vehicle_access(self):
        s=Session.__new__(Session);s.state={'paused':True};s.a=SimpleNamespace(case=CASES[1],displays_clear=True,guidance_closed=True)
        with self.assertRaisesRegex(ValueError,'Prior case'):s.case()
        s.state['control']={'passed':True,'observation':{'clear':True,'windshield_images':0}}
        with self.assertRaisesRegex(ValueError,'windshield control'):s.case()
    def test_repeat_and_unclear_block_before_vehicle_access(self):
        s=Session.__new__(Session);s.state={'paused':True,'control':{}};s.a=SimpleNamespace(case='control',displays_clear=True,guidance_closed=True)
        with self.assertRaisesRegex(ValueError,'never overwrite'):s.case()
        s.state={'paused':True};s.a.displays_clear=False
        with self.assertRaisesRegex(ValueError,'visually clear'):s.case()
    def test_restoration_required_even_with_all_test_cleanup(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);state={c:{'passed':True,'observation':{'clear':True}}for c in CASES}
            (root/'state.json').write_text(json.dumps(state));self.assertFalse(audit(root)['complete'])
            state['restoration']={'verified':True};(root/'state.json').write_text(json.dumps(state));self.assertTrue(audit(root)['complete'])
            state[CASES[2]]['observation']['clear']=False;(root/'state.json').write_text(json.dumps(state));self.assertFalse(audit(root)['complete'])
    def test_changed_source_rejected_before_ssh(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);(root/'kit.json').write_text(json.dumps({'source_sha256':{'manage_road_list_session.py':'wrong'}}))
            with self.assertRaisesRegex(ValueError,'Prepared source changed'):Session(SimpleNamespace(output=root,command='pause',execute=True,ssh_socket='missing'))
if __name__=='__main__':unittest.main()
