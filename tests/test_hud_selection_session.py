import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_hud_selection_session import audit, capture_valid, cleanup_ok, advancing, last_frame, save, output_empty

class SessionGates(unittest.TestCase):
    def recording(self):
        data=struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,1)+struct.pack('<IIII',0,0,1,1)+b'x'
        summary=dict(reason='duration',elapsed_s=120,packets=1,pcap_bytes=len(data),drops=0,interface_drops=0)
        return data,summary
    def test_recording_integrity(self):
        data,s=self.recording()
        text=lambda: json.dumps(dict(ready=True,duration_s=120))+'\n'+json.dumps(s)
        self.assertTrue(capture_valid(data,text()))
        for key,value in [('drops',1),('interface_drops',1),('reason','limit'),('packets',2),('elapsed_s',30),('pcap_bytes',0)]:
            old=s[key];s[key]=value
            self.assertFalse(capture_valid(data,text()),key);s[key]=old
        self.assertFalse(capture_valid(data[:-1],text()))
    def test_output_must_have_no_windows_or_sources(self):
        raw=b'device_id = OTHER2\nwindows = (none)\n  source = (none)\n'
        self.assertTrue(output_empty(raw))
        self.assertFalse(output_empty(raw.replace(b'windows = (none)',b'windows = 9001')))
        self.assertFalse(output_empty(raw.replace(b'source = (none)',b'source = 9001')))
        self.assertFalse(output_empty(b''))
    def test_cleanup_cannot_pass_partial(self):
        r=dict(status='finished',local_cleanup=True,protocol_cleanup=True,resource_absent=True)
        self.assertTrue(cleanup_ok(r))
        for key in r:
            bad=dict(r);bad.pop(key);self.assertFalse(cleanup_ok(bad))
    def test_heartbeat_not_drawing_proof(self):
        f=dict(frame=10,sample_ms=100,rpm=650)
        self.assertFalse(advancing(f,dict(f)))
        self.assertFalse(advancing(f,dict(frame=11,sample_ms=100,rpm=650)))
        self.assertTrue(advancing(f,dict(frame=11,sample_ms=200,rpm=650)))
        self.assertEqual(last_frame(b'{"ack":3}\n'+json.dumps(f).encode()),f)
        with self.assertRaises(ValueError): last_frame(b'{"ack":3}')
    def test_completeness_requires_both_cases_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state={};save(root/'state.json',state)
            self.assertFalse(audit(root)['complete'])
            for c in ('control461','contrast69'):
                (root/c).mkdir();save(root/c/'result.json',dict(status='finished',local_cleanup=True,protocol_cleanup=True,resource_absent=True))
                state[c]=dict(capture_valid=True,remote_removed=True,observation=dict(location='cluster',displays_clear=True))
            save(root/'state.json',state);self.assertFalse(audit(root)['complete'])
            state['restoration']=dict(verified=True);save(root/'state.json',state)
            self.assertTrue(audit(root)['complete']);self.assertFalse(audit(root)['windshield_success'])
            state['contrast69']['observation']['displays_clear']=False;save(root/'state.json',state)
            self.assertFalse(audit(root)['complete'])

if __name__=='__main__':unittest.main()
