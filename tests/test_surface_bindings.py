import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import collect_surface_bindings as c
class BindingTests(unittest.TestCase):
    def args(self,root):return SimpleNamespace(output=Path(root)/'capture',head='169.254.199.119',local='169.254.1.2',known_hosts=Path(root)/'known',socket=None)
    def test_plan_is_no_network(self):
        with patch.object(sys,'argv',['capture']),patch.object(c.subprocess,'run') as r,patch('builtins.print'):
            self.assertEqual(c.main(),0);r.assert_not_called()
    def test_exact_files_double_read(self):
        commands=[]
        def fake(argv,**kw):
            commands.append(argv[-1]);return subprocess.CompletedProcess(argv,0,b'QNX hu-omap 6.5.0 armle' if argv[-1]=='uname -a' else b'example=value\n',b'')
        with tempfile.TemporaryDirectory() as d,patch.object(c.subprocess,'run',side_effect=fake):
            a=self.args(d);self.assertTrue(c.collect(a));r=json.loads((a.output/'manifest.json').read_text());self.assertEqual(len(r),3);self.assertTrue(all(x['double_read_match'] for x in r))
        self.assertEqual(len(commands),7);self.assertTrue(all(x=='uname -a' or x.startswith('dd if=') for x in commands))
    def test_wrong_host_stops_before_files(self):
        with tempfile.TemporaryDirectory() as d,patch.object(c.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'Other platform',b'')) as r:
            with self.assertRaises(ValueError):c.collect(self.args(d))
            self.assertEqual(r.call_count,1)
    def test_changed_file_is_not_saved(self):
        count=[0]
        def fake(argv,**kw):
            count[0]+=1;data=b'QNX hu-omap armle' if count[0]==1 else str(count[0]).encode()
            return subprocess.CompletedProcess(argv,0,data,b'')
        with tempfile.TemporaryDirectory() as d,patch.object(c.subprocess,'run',side_effect=fake):
            a=self.args(d);self.assertFalse(c.collect(a));self.assertTrue(all(x['status']=='unstable_or_failed_repeat' for x in json.loads((a.output/'manifest.json').read_text())))
if __name__=='__main__':unittest.main()
