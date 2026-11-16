import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from renderer_evidence import inspect, inspect_file

class RendererEvidenceTests(unittest.TestCase):
    def test_client_is_not_server(self):
        r=inspect(b'\x7fELF CSomeIPRICServiceGuidanceClientBase')
        self.assertIn('ric_client',r['signatures'])
        self.assertNotIn('ric_server_lead',r['signatures'])
        self.assertFalse(r['server_implementation_proven'])

    def test_server_name_is_only_a_lead(self):
        r=inspect(b'RICServiceGuidanceSomeIPStubAdapter RbRicService')
        self.assertEqual(r['signatures']['ric_server_lead']['count'],2)
        self.assertFalse(r['server_implementation_proven'])
        self.assertFalse(r['live_drawing_allowed'])

    def test_session_substring_not_ramses(self):
        self.assertEqual(inspect(b'getParamSessionInside')['signatures'],{})

    def test_dcsm_separate_from_ric(self):
        r=inspect(b'de.bmw.infotainment.dcsm.Dcsm2\0DCSM2 WATCHDOG TIMEOUT\0libramses.so')
        self.assertEqual(set(r['signatures']),{'dcsm2_interface','dcsm2_watchdog','ramses_library'})

    def test_offsets_are_bounded_but_count_preserved(self):
        r=inspect(b'RamsesClient\0'*40)
        self.assertEqual(r['signatures']['ramses_api']['count'],40)
        self.assertEqual(len(r['signatures']['ramses_api']['offsets']),32)

    def test_regular_file_only(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'input';p.write_bytes(b'\x7fELF')
            self.assertTrue(inspect_file(p)['elf'])
            q=Path(t)/'link';q.symlink_to(p)
            for f in (q,Path(t)):
                with self.assertRaises(ValueError):inspect_file(f)
