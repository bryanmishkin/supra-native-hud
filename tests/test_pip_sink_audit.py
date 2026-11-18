import math
from pathlib import Path
import struct
import subprocess
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_pip_sink import decode


def packet(method,kind,body):
    return struct.pack('>HHIHHBBBB',0xb009,method,len(body)+8,1,0,1,1,kind,0)+body


class SinkAuditTests(unittest.TestCase):
    def test_retained_factory_shapes(self):
        event=packet(0x8001,2,bytes.fromhex('3ff000000000000001cc00ed01'))
        self.assertEqual(decode(event),dict(type='selection',scale=1.0,width=460,height=237,selection=1))
        self.assertEqual(decode(packet(1,1,b'\x01\0')),dict(type='completion',selection=1,status=0))
        for n in range(len(event)):
            with self.assertRaises(ValueError):decode(event[:n])

    def test_unsupported_events_do_not_become_readiness(self):
        for scale,w,h,s in [(math.nan,460,237,1),(math.inf,460,237,1),(0,460,237,1),(1,0,237,1),(1,460,0,1),(1,460,237,2)]:
            with self.assertRaises(ValueError):decode(packet(0x8001,2,struct.pack('>dHHB',scale,w,h,s)))
        for body in [b'\x01\x01',b'\x02\0',b'\0']:
            with self.assertRaises(ValueError):decode(packet(1,1,body))

    def test_retired_live_entry_rejects_before_reading_or_connecting(self):
        tool=Path(__file__).resolve().parents[1]/'tools/pip_trial.py'
        r=subprocess.run([sys.executable,str(tool),'--execute','--create-response','/does-not-exist',
                          '--support-profile','/does-not-exist','--output','/does-not-exist'],capture_output=True,text=True)
        self.assertEqual(r.returncode,2)
        self.assertIn('Live PiP runner retired',r.stderr)
        self.assertNotIn('Traceback',r.stderr)
