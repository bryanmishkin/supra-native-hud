import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import run_passive_capture as runner
from test_extract_pcap import pcap,packet

class RunnerTests(unittest.TestCase):
    def test_dry_run_never_calls_ssh(self):
        with patch.object(sys,'argv',['runner','--host','root@169.254.199.119','--output','unused']),patch.object(runner.subprocess,'run') as call,patch('builtins.print'):
            self.assertEqual(runner.main(),0);call.assert_not_called()
    def test_reject_shell_metacharacters(self):
        for host,interface in [('root@1.2.3.4;true','vlan73'),('root@1.2.3.4','vlan73;true')]:
            with self.assertRaises(ValueError):runner.validate(host,interface,'baseline')
    def test_upload_readback_capture_and_cleanup(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);binary=base/'binary';binary.write_bytes(b'candidate')
            manifest=base/'manifest';manifest.write_text(json.dumps(dict(sha256=hashlib.sha256(b'candidate').hexdigest(),static_gate_passed=True)))
            capture=pcap(packet(1,b'partial stream'))
            summary=json.dumps(dict(reason='duration',elapsed_s=15,packets=1,drops=0,interface_drops=0,pcap_bytes=len(capture))).encode()
            commands=[]
            def fake(argv,**kw):
                cmd=argv[-1];commands.append(cmd);out=b'';err=b''
                if cmd=='ifconfig vlan73':out=b'vlan73: flags=1<UP>\n inet 160.48.199.119 netmask 0xffffff80\n'
                elif cmd.startswith('cat /fs/ram5/'):out=b'candidate'
                elif ' --capture ' in cmd:out=capture;err=summary
                return subprocess.CompletedProcess(argv,0,out,err)
            args=['runner','--host','root@169.254.199.119','--output',str(base/'result'),'--binary',str(binary),'--manifest',str(manifest),'--execute']
            with patch.object(sys,'argv',args),patch.object(runner.subprocess,'run',side_effect=fake):self.assertEqual(runner.main(),0)
            r=json.loads((base/'result/result.json').read_text());self.assertTrue(r['cleanup_verified']);self.assertTrue(r['capture_valid'])
            self.assertTrue(commands[-1].startswith('rm -f /fs/ram5/supra-capture-'))
if __name__=='__main__':unittest.main()
