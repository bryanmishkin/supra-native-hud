import sys,unittest,tempfile,subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import collect_pip_phase as c
class PhaseTests(unittest.TestCase):
    def args(self,p):return SimpleNamespace(output=Path(p),phase='normal')
    def test_plan_has_no_transport(self):
        with patch.object(c.subprocess,'run',side_effect=AssertionError('network')):
            self.assertFalse(c.plan()['remote_writes'])
            self.assertEqual(len(c.plan()['phases']),7)
    def test_wrong_identity_stops_before_inventory(self):
        with tempfile.TemporaryDirectory() as p,patch.object(c.runtime,'ssh_args',side_effect=lambda a,x:x),patch.object(c.subprocess,'run',return_value=subprocess.CompletedProcess('',0,b'Linux',b'')) as call:
            with self.assertRaises(ValueError):c.collect(self.args(p))
            self.assertEqual(call.call_count,1)
    def test_missing_screen_is_not_success(self):
        def run(cmd,**kw):
            if cmd=='uname -a':return subprocess.CompletedProcess(cmd,0,b'QNX hu-omap armle',b'')
            return subprocess.CompletedProcess(cmd,1 if '/dev/screen' in cmd else 0,b'',b'')
        with tempfile.TemporaryDirectory() as p,patch.object(c.runtime,'ssh_args',side_effect=lambda a,x:x),patch.object(c.subprocess,'run',side_effect=run):
            r=c.collect(self.args(p));self.assertFalse(r['phase_metadata_complete'])
            self.assertFalse(r['windshield_routing_proven'])
            with self.assertRaises(FileExistsError):c.collect(self.args(p))
