"""Completion gates only: these fixtures do not represent a live vehicle test."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from pip_exploration import verify,PHASES

class CompletionTests(unittest.TestCase):
    def test_missing_phases_and_cleanup_never_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); rec=root/'recording';rec.mkdir();raw=b'fixture'
            (rec/'traffic.pcap').write_bytes(raw)
            (rec/'result.json').write_text(json.dumps({'sha256':hashlib.sha256(raw).hexdigest(),'capture_valid':True,'cleanup_verified':False}))
            with patch('pip_exploration.audit',return_value={'errors':[]}):r=verify(root,rec)
            self.assertFalse(r['technical_capture_complete'])
            self.assertIn('recorder cleanup unverified',r['failures'])
            self.assertIn('missing phase restored',r['failures'])
    def test_short_final_hold_and_changed_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);rec=root/'recording';rec.mkdir();raw=b'fixture'
            (rec/'traffic.pcap').write_bytes(raw)
            (rec/'result.json').write_text(json.dumps({'sha256':hashlib.sha256(raw).hexdigest(),'capture_valid':True,'cleanup_verified':True,'clock_sample':{'valid_numeric_epoch':True},'ready_seen_epoch':100,'host_start_epoch':100,'stats':{'elapsed_s':75}}))
            for label in ('v1-before','v1-after'):(root/(label+'.json')).write_text('{"all_15_match":true}')
            for phase,stamp in zip(PHASES,(100,120,140,170)):
                (root/(phase+'.json')).write_text(json.dumps({'phase':phase,'host_epoch':stamp,'observation':'fixture','snapshots_ok':True,'commands':[{'name':'surface','sha256':'missing'}]}))
            with patch('pip_exploration.audit',return_value={'errors':[]}):r=verify(root,rec)
            self.assertFalse(r['technical_capture_complete'])
            self.assertIn('insufficient capture coverage restored',r['failures'])
            self.assertIn('snapshot hash mismatch original',r['failures'])
if __name__=='__main__':unittest.main()
