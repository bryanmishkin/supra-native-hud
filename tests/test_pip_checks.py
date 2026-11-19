import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_pip_checks import audit_streams

F = ['a', 1, 'b', 2]
R = ['b', 2, 'a', 1]

def packet(kind, body):
    return struct.pack('>HHIHHBBBB', 0xb006, 2, len(body)+8, 1, 2, 1, 1, kind, 0)+body

def stream(flow, data, error=None):
    return dict(flow=flow, data=data, parse_error=error)

REQ = packet(0, struct.pack('>IIB', 200, 0x02000004, 2))
YES = packet(128, b'\1')

class Checks(unittest.TestCase):
    def test_exact_reverse_pair(self):
        r=audit_streams([stream(F,REQ),stream(R,YES)])
        self.assertTrue(r['transactions'][0]['unambiguous'])
        self.assertTrue(r['transactions'][0]['responses'][0]['check_result'])
        self.assertFalse(r['visible_pixels_proven'])
    def test_same_ids_different_connection_not_paired(self):
        r=audit_streams([stream(F,REQ),stream(['b',2,'a',3],YES)])
        self.assertEqual(r['transactions'][0]['responses'], [])
    def test_reused_session_ambiguous(self):
        r=audit_streams([stream(F,REQ+REQ),stream(R,YES)])
        self.assertFalse(r['transactions'][0]['unambiguous'])
    def test_complete_prefix_only(self):
        r=audit_streams([stream(F,REQ+REQ[:17], 'truncated body at offset %d'%len(REQ))])
        self.assertEqual(len(r['transactions']),1)
        self.assertEqual(r['recovered_prefixes'][0]['bytes'],len(REQ))
    def test_no_scan_after_unknown_error(self):
        r=audit_streams([stream(F,b'garbage'+REQ,'unsupported protocol at offset 0')])
        self.assertEqual(r['transactions'],[])
        self.assertEqual(len(r['rejected_streams']),1)

if __name__ == '__main__': unittest.main()
