import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
s=importlib.util.spec_from_file_location('kit',Path(__file__).parents[1]/'tools/prepare_car_kit.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class KitTest(unittest.TestCase):
    def make(self,root):
        b=root/'build';a=root/'audits';b.mkdir();a.mkdir()
        for n in m.CANDIDATES:
            data=('test-'+n).encode();(b/n).write_bytes(data)
            (a/(n+'.audit.json')).write_text(json.dumps({'static_gate_passed':True,'candidate':{'sha256':hashlib.sha256(data).hexdigest()}}))
        return b,a
    def test_stale_audit_blocks_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);b,a=self.make(r);(b/m.CANDIDATES[0]).write_bytes(b'changed')
            with self.assertRaises(ValueError):m.prepare(b,a,r/'out')
            self.assertFalse((r/'out').exists())
    def test_separate_opt_in_observer_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);b,a=self.make(r);m.prepare(b,a,r/'out')
            self.assertNotIn('observer',(r/'out/run-selftest.sh').read_text())
            self.assertFalse(json.loads((r/'out/manifest.json').read_text())['car_tested'])
            with self.assertRaises(FileExistsError):m.prepare(b,a,r/'out')
if __name__=='__main__':unittest.main()
