import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_owned_session import OwnedSession,RicFailure

class ScriptedTransport:
    def __init__(self, steps):self.steps=list(steps);self.methods=[];self.packets=[]
    def __call__(self, packet, timeout):
        self.packets.append(packet);method=struct.unpack_from('>H',packet,2)[0];self.methods.append(method)
        expected,result=self.steps.pop(0)
        assert expected==method,(expected,method)
        assert 0<timeout<=5
        if isinstance(result,Exception):raise result
        if callable(result):return result(packet)
        header=bytearray(packet[:16]);header[4:8]=struct.pack('>I',len(result)+8);header[14]=0x80
        return bytes(header)+result

def create(handle=1234):return struct.pack('>II',handle,0)
def session(t):return OwnedSession(t,['offline.test','test','test'],[3,3,1],7)

class OwnedSessionTests(unittest.TestCase):
    def test_complete_resource_lifecycle(self):
        t=ScriptedTransport([(1,create()),(2,b'\0'),(3,b''),(2,b'\1'),(8,b''),(2,b'\0'),(7,b'')])
        with session(t) as s:s.upload_bitmap(9,1,[1,1],b'x')
        self.assertEqual(t.methods,[1,2,3,2,8,2,7]);self.assertFalse(t.steps)
        self.assertFalse(s.cleanup_report['resources'][0]['post_dispose_check'])
        self.assertTrue(s.cleanup_report['instance_dispose_acknowledged'])
        self.assertFalse(s.cleanup_report['visual_test_passed'])
        self.assertFalse(s.cleanup_report['remote_image_erased'])
        for p in t.packets[1:]:self.assertEqual(struct.unpack_from('>I',p,16)[0],1234)
    def test_lost_upload_reply_still_disposes(self):
        t=ScriptedTransport([(1,create()),(2,b'\0'),(3,TimeoutError('lost upload reply')),(8,b''),(2,b'\0'),(7,b'')])
        s=session(t);s.open()
        with self.assertRaises(TimeoutError):s.upload_bitmap(9,1,[1,1],b'x')
        self.assertEqual(t.methods[-3:],[8,2,7]);self.assertFalse(t.steps)
    def test_dispose_failure_still_checks_and_releases_instance(self):
        t=ScriptedTransport([(1,create()),(2,b'\0'),(3,b''),(2,b'\1'),(8,TimeoutError()),(2,b'\1'),(7,b'')])
        with session(t) as s:s.upload_bitmap(9,1,[1,1],b'x')
        r=s.cleanup_report['resources'][0];self.assertFalse(r['dispose_acknowledged']);self.assertTrue(r['post_dispose_check'])
        self.assertTrue(s.cleanup_report['instance_dispose_acknowledged'])
    def test_lost_create_no_retry_or_guessed_dispose(self):
        t=ScriptedTransport([(1,TimeoutError())]);s=session(t)
        with self.assertRaises(TimeoutError):s.open()
        self.assertTrue(s.cleanup_report['create_result_unknown']);self.assertEqual(t.methods,[1])
        with self.assertRaises(RicFailure):s.open()
    def test_factory_handle_never_used_or_disposed(self):
        t=ScriptedTransport([(1,create(200))]);s=session(t)
        with self.assertRaises(RicFailure):s.open()
        self.assertEqual(t.methods,[1]);self.assertIsNone(s.handle)
    def test_malformed_configuration_releases_returned_handle(self):
        t=ScriptedTransport([(1,struct.pack('>II',1234,100)),(7,b'')]);s=session(t)
        with self.assertRaises(ValueError):s.open()
        self.assertTrue(s.cleanup_report['instance_dispose_acknowledged'])
    def test_existing_resource_not_overwritten_or_disposed(self):
        t=ScriptedTransport([(1,create()),(2,b'\1'),(7,b'')]);s=session(t);s.open()
        with self.assertRaises(RicFailure):s.upload_bitmap(9,1,[1,1],b'x')
        s.close();self.assertEqual(t.methods,[1,2,7])
    def test_close_idempotent(self):
        t=ScriptedTransport([(1,create()),(7,b'')]);s=session(t);s.open();a=s.close();self.assertIs(a,s.close());self.assertEqual(t.methods,[1,7])
    def test_uncorrelated_reply_does_not_allocate(self):
        def wrong(p):
            h=bytearray(p[:16]);h[4:8]=struct.pack('>I',16);h[10:12]=b'\0\x64';h[14]=0x80
            return bytes(h)+create()
        t=ScriptedTransport([(1,wrong)]);s=session(t)
        with self.assertRaises(RicFailure):s.open()
        self.assertIsNone(s.handle)
    def test_instance_release_error_is_visible(self):
        t=ScriptedTransport([(1,create()),(7,TimeoutError('lost dispose reply'))]);s=session(t);s.open();r=s.close()
        self.assertFalse(r['instance_dispose_acknowledged']);self.assertIn('lost dispose reply',r['instance_error'])
    def test_invalid_input_sends_nothing(self):
        t=ScriptedTransport([])
        with self.assertRaises(ValueError):OwnedSession(t,['BMW.IC.Guidance','a','b'],[3,3,1],7)
        self.assertFalse(t.methods)
    def test_exception_in_context_still_releases(self):
        t=ScriptedTransport([(1,create()),(7,b'')]);s=session(t)
        with self.assertRaisesRegex(RuntimeError,'original'):
            with s:raise RuntimeError('original')
        self.assertEqual(t.methods,[1,7])
