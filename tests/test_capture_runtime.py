import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import unittest
s=importlib.util.spec_from_file_location('capture',Path(__file__).parents[1]/'tools/capture_runtime.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CaptureTest(unittest.TestCase):
    def args(self,d):return SimpleNamespace(output=Path(d)/'capture',local='169.254.70.38',head='169.254.199.119',known_hosts=Path(d)/'known',socket=None)
    def fake(self,argv,**kwargs):
        command=argv[-1]
        value=b'QNX hu-omap 6.5.0 armle' if command=='uname -a' else (b'\x7fELF\x01\x01test' if command.startswith('dd ') else b'capture')
        return SimpleNamespace(returncode=0,stdout=value,stderr=b'')
    def test_no_network_default(self):
        with patch('sys.argv',['capture']),patch.object(m.subprocess,'run') as r,patch('builtins.print'):
            m.main();r.assert_not_called()
    def test_direct_omap_required(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=b'QNX hu-jacinto armle',stderr=b'')) as r:
            with self.assertRaises(SystemExit):m.run(self.args(d))
            self.assertEqual(r.call_count,1)
    def test_duplicate_capture_and_manifest(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m.subprocess,'run',side_effect=self.fake),patch('builtins.print'):
            a=self.args(d);m.run(a)
            self.assertEqual(len(m.json.loads((a.output/'manifest.json').read_text())),len(m.LIBRARIES))
    def test_changed_binary_rejected(self):
        n=0
        def changing(argv,**kw):
            nonlocal n
            r=self.fake(argv,**kw)
            if argv[-1].startswith('dd '):n+=1;r.stdout+=bytes([n])
            return r
        with tempfile.TemporaryDirectory() as d,patch.object(m.subprocess,'run',side_effect=changing):
            with self.assertRaisesRegex(SystemExit,'inconsistent'):m.run(self.args(d))
    def test_reject_other_networks(self):
        for ip in ['127.0.0.1','10.0.0.1','169.254.255.1']:
            with self.assertRaises(Exception):m.link_local(ip)
    def test_shell_injection_rejected(self):
        with self.assertRaises(Exception):m.link_local('169.254.1.1; reboot')
if __name__=='__main__':unittest.main()
