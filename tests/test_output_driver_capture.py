import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import capture_output_driver as c

class OutputDriverTests(unittest.TestCase):
    def test_real_baseline_has_fifteen_targets(self):
        expected=json.loads(c.BASELINE.read_text())['component_sha256']
        paths=c.baseline_paths(expected)
        self.assertEqual(len(paths),15)
        self.assertEqual(paths['/opt/sys/etc/starter.cfg'],expected['system-after.cfg'])
    def test_inventory_includes_versioned_drivers_and_all_configs(self):
        self.assertEqual(c.inventory_names('graphics.conf\nlibWFD.so\nlibwfdcfg.so.0\nsubdir\n'),['graphics.conf','libWFD.so','libwfdcfg.so.0'])
    def test_inventory_rejects_shell_or_traversal(self):
        for value in ('../bad.so','x;touch.so','/other/lib.so','$(id).so','..'):
            with self.assertRaises(ValueError):c.inventory_names(value)
    def test_inventory_bounded(self):
        with self.assertRaises(ValueError):c.inventory_names('\n'.join('x%d.so'%i for i in range(257)))
    def test_hash_audit_detects_changed_and_missing_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'file';p.write_bytes(b'original')
            report={'files':{'/driver':{'status':'verified','file':'file','sha256':hashlib.sha256(b'original').hexdigest()}}}
            self.assertEqual(c.audit(root,report),[])
            p.write_bytes(b'changed');self.assertEqual(c.audit(root,report),['/driver'])
            p.unlink();self.assertEqual(c.audit(root,report),['/driver'])
if __name__=='__main__':unittest.main()
