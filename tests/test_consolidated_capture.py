import json,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import consolidated_capture as c
class ConsolidatedTests(unittest.TestCase):
    def session(self,d,fn):return c.Session(SimpleNamespace(output=Path(d)),fn)
    def reply(self,b=b'value',rc=0):return subprocess.CompletedProcess([],rc,b,b'')
    def test_default_no_network(self):
        with patch.object(sys,'argv',['capture']),patch.object(c.subprocess,'run') as r,patch('builtins.print'):
            self.assertEqual(c.main(),0);r.assert_not_called()
    def test_double_read_and_resume_revalidation(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def t(cmd,*_):calls.append(cmd);return self.reply()
            s=self.session(d,t);p=s.file('/etc/someip/services.conf');self.assertEqual(p.read_bytes(),b'value');self.assertEqual(len(calls),2)
            s=self.session(d,t);s.file('/etc/someip/services.conf');self.assertEqual(len(calls),3);self.assertEqual(s.report['files']['/etc/someip/services.conf']['status'],'reverified')
            p.write_bytes(b'corrupt');s=self.session(d,t);s.file('/etc/someip/services.conf');self.assertEqual(len(calls),5);self.assertEqual(p.read_bytes(),b'value')
    def test_changed_remote_is_not_reused(self):
        with tempfile.TemporaryDirectory() as d:
            s=self.session(d,lambda *_:self.reply(b'old'));s.file('/etc/test')
            vals=iter([b'new',b'changed']);s=self.session(d,lambda *_:self.reply(next(vals)))
            self.assertIsNone(s.file('/etc/test'));self.assertEqual(s.report['files']['/etc/test']['status'],'unstable')
    def test_missing_timeout_and_oversize_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            s=self.session(d,lambda *_:self.reply(rc=1));self.assertIsNone(s.file('/etc/missing'))
            def timeout(*_):raise subprocess.TimeoutExpired('read',45)
            s.transport=timeout;self.assertIsNone(s.file('/etc/timeout'))
            with patch.object(c,'MAX_FILE',3):
                s.transport=lambda *_:self.reply(b'1234');self.assertIsNone(s.file('/etc/large'))
            rows=s.report['files'];self.assertEqual(rows['/etc/missing']['status'],'unavailable');self.assertEqual(rows['/etc/timeout']['status'],'error');self.assertEqual(rows['/etc/large']['status'],'oversized')
    def test_wrong_host_and_unsafe_path(self):
        with tempfile.TemporaryDirectory() as d:
            s=self.session(d,lambda *_:self.reply(b'Other OS'))
            with self.assertRaises(ValueError):s.identity()
            for p in ['/etc/../secret','/etc/a;bad','/etc/$(bad)']:
                with self.assertRaises(ValueError):s.file(p)
    def test_cleanup_allowed_after_budget(self):
        with tempfile.TemporaryDirectory() as d:
            s=self.session(d,lambda *_:self.reply());s.start=time.monotonic()-1300
            with self.assertRaises(ValueError):s.call('uname -a')
            self.assertEqual(s.call('cleanup',cleanup=True).returncode,0)
if __name__=='__main__':unittest.main()

class PhaseTests(unittest.TestCase):
    session=ConsolidatedTests.session
    reply=ConsolidatedTests.reply
    def test_full_collection_missing_binary_is_not_complete(self):
        from test_arm_trace import fixture
        with tempfile.TemporaryDirectory() as d:
            def transport(cmd,*_):
                if cmd=='uname -a':return self.reply(b'QNX hu-omap 6.5 armle')
                if 'NavigationFully bs=' in cmd or 'NavCtrl_DB.ini bs=' in cmd:return self.reply(rc=1)
                if cmd.startswith('dd if='):
                    path=cmd.split('if=')[1].split()[0]
                    return self.reply(fixture() if '/bin/' in path and not path.endswith(('.ini','.cfg','.hbtc')) else b'config')
                return self.reply(b'')
            s=self.session(d,transport);s.collect();self.assertFalse(s.report['files_complete']);self.assertFalse(s.report['provider_binding_proven'])
    def test_invalid_recorder_never_uploads(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[];s=self.session(d,lambda cmd,*_:(calls.append(cmd) or self.reply()))
            p=Path(d)/'fake';p.write_bytes(b'not arm')
            with self.assertRaises(ValueError):s.record(p,c.digest(p.read_bytes()))
            self.assertEqual(calls,[])

class RecordingTests(unittest.TestCase):
    def run_fixture(self,fail_parse=False,upload_bad=False,live_process=False):
        from test_arm_trace import fixture
        from test_extract_pcap import pcap,packet
        import struct
        with tempfile.TemporaryDirectory() as d:
            a=SimpleNamespace(output=Path(d)/'out',local='169.254.1.2',head='169.254.199.119',known_hosts=Path(d)/'known',socket=None)
            binary=Path(d)/'recorder';binary.write_bytes(fixture());calls=[]
            def transport(cmd,timeout,input):
                calls.append(cmd)
                if cmd=='ifconfig vlan73':b=b'flags=<UP> inet 160.48.199.119'
                elif cmd.startswith('cat /fs/ram5/'):b=b'wrong' if upload_bad else fixture()
                elif cmd=='date +%s':b=b'1000'
                elif cmd=='pidin ar' and live_process:b=next(x for x in calls if x.startswith('chmod 700 '))[10:].encode()
                else:b=b''
                return subprocess.CompletedProcess([],0,b,b'')
            body=struct.pack('>HHIHHBBBB',0xb009,1,10,1,0,1,1,1,0)+bytes(2)
            data=b'bad capture' if fail_parse else pcap(packet(0,body))
            class FakeProcess:
                returncode=0
                def __init__(self,args,stdout,stderr):
                    stdout.write(data);stdout.flush()
                    stderr.write((json.dumps({'ready':True})+'\n'+json.dumps(dict(packets=1,pcap_bytes=len(data),elapsed_s=120,drops=0,interface_drops=0,reason='duration'))+'\n').encode());stderr.flush()
                def poll(self):return 0
            with patch.object(c.subprocess,'Popen',FakeProcess):r=c.Session(a,transport).record(binary,c.digest(binary.read_bytes()))
            self.assertTrue(any(x.startswith('rm -f /fs/ram5/shud-') for x in calls))
            self.assertFalse(any('rmdir ' in x for x in calls))
            created=next(x.split('mkdir ',1)[1] for x in calls if 'mkdir ' in x)
            self.assertLessEqual(len(Path(created).name),27)
            return r
    def test_capture_and_cleanup_are_separate_from_allocation(self):
        r=self.run_fixture();self.assertTrue(r['capture_valid']);self.assertTrue(r['cleanup_verified']);self.assertFalse(r['creation_exchange_observed']);self.assertFalse(r['startup_covered'])
    def test_parse_failure_retained_and_cleaned(self):
        r=self.run_fixture(fail_parse=True);self.assertFalse(r['capture_valid']);self.assertTrue(r['cleanup_verified']);self.assertIn('error',r)
    def test_bad_upload_never_records(self):
        r=self.run_fixture(upload_bad=True);self.assertFalse(r['capture_valid']);self.assertTrue(r['cleanup_verified'])
    def test_live_process_is_not_clean(self):
        r=self.run_fixture(live_process=True);self.assertFalse(r['cleanup_verified'])
