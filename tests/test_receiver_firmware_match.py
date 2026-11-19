import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from match_receiver_firmware import match,targets

class MatchTests(unittest.TestCase):
    # Sanitized structural fixture; tests filename matching, not real firmware.
    reply=bytes.fromhex('62f10101010002')+bytes(13)+bytes.fromhex('0800005ffb0800000700005ffa070101')
    def test_process_class_and_exact_versions(self):
        t=targets(self.reply)
        self.assertEqual([(r['kind'],r['version']) for r in t],[('swfl','008_000_000'),('flsl','007_001_001')])
    def test_wrong_version_not_accepted_and_names_not_authentication(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'swfl_00005ffb.bin.007_000_000').write_bytes(b'wrong version')
            (root/'swfl_00005ffb.bin.008_000_000').write_bytes(b'not firmware')
            r=match(self.reply,[root])
            self.assertEqual(len(r['other_versions']),1)
            self.assertEqual(len(r['exact_filename_candidates']),1)
            self.assertFalse(r['exact_filename_candidates'][0]['content_identity_verified'])
            self.assertIn('swfl_00005ffb.xml.008_000_000',r['missing_expected_names'])
            self.assertFalse(r['renderer_match_proven'])
    def test_absent_packages_remain_absent(self):
        r=match(self.reply,[])
        self.assertEqual(len(r['missing_expected_names']),4)
        self.assertFalse(r['firmware_contents_verified'])

if __name__=='__main__':unittest.main()
