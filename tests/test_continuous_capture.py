import json, os, subprocess, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).parents[1]

class ContinuousCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.binary = str(Path(cls.tmp.name)/'capture-fixture')
        subprocess.run(['cc','-Wall','-Wextra','-Werror',str(ROOT/'tools/hud_continuous_capture.c'),str(ROOT/'tests/fake_continuous_pcap.c'),'-o',cls.binary],check=True)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def run_mode(self, mode):
        r = subprocess.run([self.binary,'--capture','vlan73'],env=dict(os.environ,CAPTURE_FIXTURE=mode),capture_output=True,timeout=3)
        return r
    def test_empty_and_packets_finish(self):
        for mode, count in [('empty',0),('packets',2)]:
            r=self.run_mode(mode);self.assertEqual(r.returncode,0,r.stderr)
            report=json.loads(r.stderr.splitlines()[-1]);self.assertEqual(report['packets'],count)
            self.assertTrue(json.loads(r.stderr.splitlines()[0])['ready']);self.assertGreaterEqual(report['elapsed_s'],120)
            self.assertEqual(report['pcap_bytes'],len(r.stdout));self.assertFalse(report['promiscuous'])
    def test_limits_drops_and_io_errors_are_not_success(self):
        for mode in ['limit','drops','readerror','writeerror']:
            r=self.run_mode(mode);self.assertNotEqual(r.returncode,0)
            self.assertLessEqual(len(r.stdout),64*1024*1024)
            report=json.loads(r.stderr.splitlines()[-1]);self.assertEqual(report['transmitted'],0)
            if mode=='limit':self.assertEqual(report['reason'],'limit')
    def test_setup_errors_do_not_write_pcap(self):
        for mode in ['badlink','badfilter']:
            r=self.run_mode(mode);self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,b'')
    def test_no_default_capture(self):
        r=subprocess.run([self.binary],capture_output=True)
        self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,b'')

if __name__=='__main__':unittest.main()
