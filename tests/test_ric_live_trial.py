import json
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_live_trial import (DrawingTrial, TcpExchange, choose_allocation, marker_png,
                            list_body, SERVER_COOKIE)
from ric_owned_session import OwnedSession, RicFailure
from ric_graph import decode_graph_body
from ric_guiding import decode_guiding_body
from ric_resource import decode_resource_body


def configuration(missing=None, handle=1234):
    parts=[]
    # Deliberately non-type-prefixed IDs expose accidental shifts/replay IDs.
    for typ,tag,off in [(10,1,1001),(15,17,2001),(32,20,3001),(33,21,4001)]:
        if typ == missing:continue
        raw=struct.pack('>BBII',0,typ,1,off)
        parts.append(struct.pack('>II',len(raw),tag)+raw)
    raw=struct.pack('>BBIIHHBBBB',33,1,1,5001,64,32,0,0,1,0)
    parts.append(struct.pack('>II',len(raw),33)+raw)
    data=b''.join(parts)
    return struct.pack('>II',handle,len(data))+data


class Server:
    def __init__(self,missing=None,fail_at=None,sticky=False):
        self.missing,self.fail_at,self.sticky=missing,fail_at,sticky
        self.methods=[];self.packets=[];self.present=False
    def __call__(self,p,timeout):
        m=struct.unpack_from('>H',p,2)[0]
        self.methods.append(m);self.packets.append(p)
        if m != 1:assert struct.unpack_from('>I',p,16)[0] == 1234
        if len(self.methods)==self.fail_at:raise TimeoutError('injected timeout')
        if m==1:body=configuration(self.missing)
        elif m==2:body=bytes([self.present])
        else:
            body=b''
            if m==3:self.present=True
            if m==8 and not self.sticky:self.present=False
        h=bytearray(p[:16]);h[4:8]=struct.pack('>I',8+len(body));h[14]=0x80
        return bytes(h)+body


def trial(server,observations=(True,True,True)):
    obs=iter(observations);records=[]
    session=OwnedSession(server,('own.test','test','owner'),(3,3,1),0x5348)
    result=DrawingTrial(session,lambda x:records.append(json.loads(json.dumps(x))),
                        lambda phase,seconds:next(obs)).run()
    return result,records


class TrialTests(unittest.TestCase):
    def test_complete_lifecycle_uses_negotiated_ids(self):
        server=Server();r,records=trial(server)
        self.assertTrue(r['visual_test_passed'])
        self.assertEqual(server.methods,[1,2,3,2,9,11,10,12,4,9,9,9,12,11,4,8,2,7])
        image=decode_resource_body(server.packets[2][16:])
        self.assertEqual(image['resource_id'],5001)
        high=decode_guiding_body(server.packets[5][16:])['high_roundabout']
        self.assertEqual(high['model_id'],1001)
        self.assertEqual(high['picture_resource_id'],5001)
        desc=decode_graph_body(10,server.packets[6][16:])['description']
        self.assertEqual(desc['detailed_maneuver_id'],1001)
        self.assertEqual(desc['model_id'],2001)
        state=decode_graph_body(9,server.packets[9][16:])['list_state']
        self.assertEqual(state['active_maneuver_id'],2001)
        self.assertEqual(state['model_id'],4001)
        removed=decode_guiding_body(server.packets[13][16:])['high_roundabout']
        self.assertEqual(removed['picture_resource_id'],0xffffffff)
        self.assertGreater(len(records),10)
        self.assertFalse(r['cleanup']['remote_image_erased'])
    def test_protocol_ack_never_substitutes_for_visibility(self):
        for observed in [(False,True,True),(None,None,None),(True,False,True),(True,True,False)]:
            with self.subTest(observed=observed):
                r,_=trial(Server(),observed);self.assertFalse(r['visual_test_passed'])
    def test_missing_configuration_releases_without_upload(self):
        s=Server(missing=10);r,_=trial(s)
        self.assertEqual(s.methods,[1,7]);self.assertFalse(r['visual_test_passed'])
        self.assertIn('create_response_hex',r)
    def test_still_present_after_disposal_is_failure(self):
        r,_=trial(Server(sticky=True));self.assertFalse(r['visual_test_passed'])
        self.assertTrue(r['cleanup']['resources'][0]['post_dispose_check'])
    def test_all_post_create_failures_attempt_release(self):
        for failure in range(2,19):
            with self.subTest(failure=failure):
                s=Server(fail_at=failure);r,_=trial(s)
                self.assertIn(7,s.methods)
                self.assertFalse(r['visual_test_passed'])
    def test_interrupt_during_observation_still_withdraws(self):
        s=Server();session=OwnedSession(s,('own.test','test','owner'),(3,3,1),7)
        def obs(phase,seconds):
            if phase=='marker':raise KeyboardInterrupt()
            return True
        r=DrawingTrial(session,lambda x:None,obs).run()
        self.assertEqual(s.methods[-3:],[8,2,7]);self.assertFalse(r['visual_test_passed'])
    def test_wrong_factory_handle_sends_no_other_method(self):
        s=Server()
        def transport(p,t):
            reply=s(p,t)
            return reply[:16]+configuration(handle=200)
        r,_=trial(transport);self.assertFalse(r['visual_test_passed']);self.assertEqual(s.methods,[1])
    def test_model_offsets_are_not_type_shifted(self):
        a=choose_allocation(configuration());self.assertEqual(a['models'][10],1001)
    def test_malformed_config_fails(self):
        for body in [b'',configuration()[:-1],configuration()+b'x']:
            with self.assertRaises((ValueError,RicFailure)):choose_allocation(body)
    def test_list_matches_observed_wire_layout(self):
        expected='000000c820000000200000001d000000012000000020000000010001000000040f00000000000000000000000000'
        self.assertEqual(list_body(200,0x20000000,0x0f000000).hex(),expected)
    def test_png_size_and_header(self):
        b=marker_png(64,32);self.assertEqual(b[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack_from('>II',b,16),(64,32));self.assertLess(len(b),65506)


class TcpTests(unittest.TestCase):
    def test_fragmentation_cookie_and_recording(self):
        c,s=socket.socketpair()
        with tempfile.TemporaryDirectory() as d:
            request=struct.pack('>HHIHHBBBB',0xb006,7,12,7,1,1,1,0,0)+struct.pack('>I',1234)
            response=struct.pack('>HHIHHBBBB',0xb006,7,8,7,1,1,1,0x80,0)
            def serve():
                s.recv(100)
                for b in SERVER_COOKIE+response:s.sendall(bytes([b]))
                s.close()
            t=threading.Thread(target=serve);t.start()
            try:self.assertEqual(TcpExchange(c,d)(request,1),response)
            finally:c.close();t.join()
            self.assertEqual(len(list(Path(d).glob('*'))),3)
    def test_timeout_poisoning_prevents_more_sends(self):
        c,s=socket.socketpair()
        with tempfile.TemporaryDirectory() as d:
            tx=TcpExchange(c,d)
            try:
                with self.assertRaises(TimeoutError):tx(b'hello',0.02)
                with self.assertRaisesRegex(RicFailure,'failed earlier'):tx(b'next',1)
                self.assertEqual(s.recv(100),b'hello')
            finally:c.close();s.close()
    def test_oversized_response_rejected_before_body_read(self):
        c,s=socket.socketpair()
        with tempfile.TemporaryDirectory() as d:
            s.sendall(struct.pack('>HHIHHBBBB',0xb006,1,0xffffffff,7,1,1,1,0x80,0))
            try:
                with self.assertRaisesRegex(RicFailure,'length'):TcpExchange(c,d)(b'hello',1)
            finally:c.close();s.close()
    def test_actual_cli_through_local_tcp_server(self):
        server=Server();listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1)
        port=listener.getsockname()[1];errors=[]
        def serve():
            try:
                conn,_=listener.accept();conn.settimeout(3)
                with conn:
                    while True:
                        def read(n):
                            b=b''
                            while len(b)<n:
                                part=conn.recv(n-len(b))
                                if not part:raise EOFError()
                                b+=part
                            return b
                        try:header=read(16)
                        except EOFError:break
                        body=read(struct.unpack_from('>I',header,4)[0]-8)
                        conn.sendall(server(header+body,2))
            except Exception as e:errors.append(e)
            finally:listener.close()
        t=threading.Thread(target=serve);t.start()
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'run'
            p=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'tools/ric_live_trial.py'),
                '--live','--host','127.0.0.1','--port',str(port),'--output',str(out)],
                input='',text=True,capture_output=True,timeout=10)
            t.join(4);self.assertFalse(t.is_alive());self.assertFalse(errors)
            self.assertEqual(p.returncode,2,p.stderr)
            r=json.loads((out/'result.json').read_text())
            self.assertEqual(r['status'],'inconclusive')
            self.assertTrue(r['cleanup']['instance_dispose_acknowledged'])
            self.assertEqual(len(list(out.glob('*-request.bin'))),18)
            self.assertEqual(len(list(out.glob('*-response.bin'))),18)
    def test_default_cli_is_offline(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'run'
            p=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'tools/ric_live_trial.py'),
                '--output',str(out)],capture_output=True,text=True,timeout=3)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads((out/'result.json').read_text())['status'],'prepared_no_network')

class LauncherTests(unittest.TestCase):
    def test_forward_commands_keep_host_verification_and_cancel(self):
        from types import SimpleNamespace
        from run_live_drawing_test import commands
        a=SimpleNamespace(local='169.254.1.2',head='169.254.1.3',known_hosts=Path('/tmp/known'),socket=Path('/tmp/master'))
        start,cancel=commands(a,34567)
        self.assertIn('StrictHostKeyChecking=yes',start)
        self.assertIn('127.0.0.1:34567:160.48.199.96:30502',start)
        self.assertEqual(start[-1],'root@169.254.1.3')
        self.assertIn('forward',start);self.assertIn('cancel',cancel)
        a.socket=None;start,cancel=commands(a,34567)
        self.assertIn('ExitOnForwardFailure=yes',start);self.assertIn('-N',start)
        self.assertIsNone(cancel)
    def test_launcher_with_local_ssh_standin_runs_and_closes(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ssh=root/'ssh';known=root/'known';known.write_text('test')
            ssh.write_text('#!'+sys.executable+'\n'+'''import sys,socket,struct
if sys.argv[-1]=='uname -a':
 print('QNX hu-omap 6.5.0 armle');sys.exit(0)
f=sys.argv[sys.argv.index('-L')+1];port=int(f.split(':')[1])
s=socket.socket();s.bind(('127.0.0.1',port));s.listen(1)
c,_=s.accept();present=False
with c:
 def read(n):
  b=b''
  while len(b)<n:
   part=c.recv(n-len(b))
   if not part:raise EOFError()
   b+=part
  return b
 while True:
  try:h=bytearray(read(16))
  except EOFError:break
  body=read(struct.unpack_from('>I',h,4)[0]-8)
  m=struct.unpack_from('>H',h,2)[0]
  if m==1:reply=bytes.fromhex(CONFIG)
  elif m==2:reply=bytes([present])
  else:
   reply=b''
   if m==3:present=True
   if m==8:present=False
  h[4:8]=struct.pack('>I',len(reply)+8);h[14]=128
  c.sendall(bytes(h)+reply)
'''.replace('CONFIG',repr(configuration().hex())))
            ssh.chmod(0o755)
            p=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'tools/run_live_drawing_test.py'),
                '--execute','--head','169.254.1.3','--local','169.254.1.2','--known-hosts',str(known),'--output',str(root/'run')],
                env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH']},input='',text=True,capture_output=True,timeout=15)
            self.assertEqual(p.returncode,2,p.stderr)
            report=json.loads((root/'run/launcher.json').read_text())
            self.assertTrue(report['forward_started']);self.assertTrue(report['forward_cancelled'])
            self.assertTrue(json.loads((root/'run/trial/result.json').read_text())['cleanup']['instance_dispose_acknowledged'])
