from pathlib import Path
import sys
import unittest
from unittest.mock import patch
TOOLS=Path(__file__).resolve().parents[1]/'tools'
sys.path.insert(0,str(TOOLS))
import run_hud_diagnostic_surface as m

class DiagnosticSurfaceTests(unittest.TestCase):
    def run_case(self,outcomes,interrupt=False,case='rgb'):
        calls=[];events=[]
        def exchange(req):
            calls.append(req)
            item=outcomes.pop(0) if outcomes else b'\x71'+req[1:4]
            if isinstance(item,BaseException):raise item
            return item
        def watch(seconds):
            self.assertEqual(seconds,30)
            if interrupt:raise KeyboardInterrupt()
        try:m.trial(exchange,case,lambda event,**kw:events.append((event,kw)),watch)
        except BaseException as e:return calls,events,e
        return calls,events,None
    def test_success(self):
        calls,events,error=self.run_case([])
        self.assertIsNone(error);self.assertEqual(calls,[m.STOP,m.CASES['rgb'],m.STOP])
    def test_all_prepared_cases_and_lost_start_cleanup(self):
        for case in m.CASES:
            with self.subTest(case=case):
                calls,events,error=self.run_case([],case=case)
                self.assertIsNone(error)
                self.assertEqual(calls,[m.STOP,m.CASES[case],m.STOP])
                calls,events,error=self.run_case([bytes.fromhex('7102a102'),TimeoutError()],case=case)
                self.assertIsInstance(error,TimeoutError)
                self.assertEqual(calls,[m.STOP,m.CASES[case],m.STOP])
    def test_preflight_lost_no_start(self):
        calls,events,error=self.run_case([TimeoutError()])
        self.assertIsInstance(error,TimeoutError);self.assertEqual(calls,[m.STOP])
    def test_stop_rejected_no_start(self):
        calls,events,error=self.run_case([bytes.fromhex('7f3122')])
        self.assertIsInstance(error,RuntimeError);self.assertEqual(calls,[m.STOP])
    def test_start_lost_or_rejected_always_stops(self):
        for failure in [TimeoutError(),ConnectionError(),bytes.fromhex('7f3131'),b'\x71\x01\xa1\x03']:
            with self.subTest(failure=failure):
                calls,events,error=self.run_case([b'\x71\x02\xa1\x02',failure])
                self.assertIsNotNone(error);self.assertEqual(calls[-1],m.STOP)
    def test_interruption_stops(self):
        calls,events,error=self.run_case([],True)
        self.assertIsInstance(error,KeyboardInterrupt);self.assertEqual(calls[-1],m.STOP)
    def test_cleanup_retries_bounded(self):
        calls,events,error=self.run_case([b'\x71\x02\xa1\x02',b'\x71\x01\xa1\x02',TimeoutError(),TimeoutError(),TimeoutError()])
        self.assertEqual(calls,[m.STOP,m.CASES['rgb'],m.STOP,m.STOP,m.STOP])
        self.assertIn('STOP NOT ACKNOWLEDGED',str(error))
    def test_cleanup_retry_success(self):
        calls,events,error=self.run_case([b'\x71\x02\xa1\x02',b'\x71\x01\xa1\x02',TimeoutError(),b'\x71\x02\xa1\x02'])
        self.assertIsNone(error);self.assertEqual(len(calls),4)
    def test_no_socket_by_default(self):
        with patch.object(sys,'argv',['runner']),patch.object(m.socket,'socket',side_effect=AssertionError('network')):
            m.main()
    def test_hsfz_matching_and_pending(self):
        frame=lambda kind,payload:m.struct.pack('>IH',len(payload),kind)+payload
        incoming=(frame(2,b'\xf4\x60'+m.STOP)+frame(1,bytes.fromhex('61f47102a102'))+
                  frame(1,bytes.fromhex('60f47f3178'))+frame(1,bytes.fromhex('60f47102a103'))+
                  frame(1,bytes.fromhex('60f47102a102')))
        class Fake:
            def __init__(self):self.data=incoming;self.sent=[]
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def settimeout(self,*args):pass
            def bind(self,*args):pass
            def connect(self,*args):pass
            def sendall(self,data):self.sent.append(data)
            def recv(self,n):data=self.data[:n];self.data=self.data[n:];return data
        fake=Fake()
        with patch.object(m.socket,'socket',return_value=fake):
            reply=m.Exchange('gateway','source',None,lambda *a,**k:None)(m.STOP)
        self.assertEqual(reply,bytes.fromhex('7102a102'))
        self.assertEqual(fake.sent,[bytes.fromhex('000000060001f4603102a102')])
    def test_allowlist_before_socket(self):
        with patch.object(m.socket,'socket',side_effect=AssertionError('network')):
            with self.assertRaises(ValueError):m.Exchange('x','y',None,lambda *a,**k:None)(bytes.fromhex('1003'))

if __name__=='__main__':unittest.main()
