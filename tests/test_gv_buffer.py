import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from inspect_gv_buffer import inspect, REUSABLE


def buffer(sequence=REUSABLE, kind=0x7000e, payload=b'abcd'):
    return struct.pack('<IIIII', 0x80000000, 0, sequence, kind, len(payload)) + payload


class BufferTests(unittest.TestCase):
    def test_reusable_retains_data_but_never_claims_destination(self):
        r = inspect(buffer() + b'old trailing bytes')
        self.assertTrue(r['reusable'])
        self.assertEqual(r['chunks'][0]['name'], 'ManeuverState')
        self.assertEqual(len(r['chunks']), 1)
        self.assertFalse(r['windshield_destination_proven'])

    def test_reject_reusable_even_when_event_matches(self):
        with self.assertRaises(ValueError): inspect(buffer(), 24, REUSABLE)

    def test_event_bounded_excludes_stale_tail(self):
        data = buffer(7) + struct.pack('<II', 0x80001, 0) + b'old tail'
        r = inspect(data, 32, 7)
        self.assertEqual([x['name'] for x in r['chunks']], ['ManeuverState', 'LabelContainer'])
        self.assertEqual(r['uninterpreted_bytes'], 8)

    def test_sequence_mismatch(self):
        with self.assertRaises(ValueError): inspect(buffer(7), 24, 8)

    def test_event_bounds(self):
        for length in [0, 19, 23, 25]:
            with self.assertRaises(ValueError): inspect(buffer(7), length, 7)

    def test_partial_event_header(self):
        with self.assertRaises(ValueError): inspect(buffer(7) + b'x', 25, 7)

    def test_missing_event_metadata(self):
        with self.assertRaises(ValueError): inspect(buffer(), 24)
        with self.assertRaises(ValueError): inspect(buffer(), event_sequence=1)

    def test_oversized_chunk(self):
        data = struct.pack('<IIIII', 0, 0, 1, 2, 0xffffffff)
        with self.assertRaises(ValueError): inspect(data)

    def test_unknown_type_preserved(self):
        self.assertEqual(inspect(buffer(kind=0xdeadbeef))['chunks'][0]['name'], 'unknown')

    def test_short_or_oversized_allocation(self):
        for data in [b'', b'x' * 19, b'x' * 262145]:
            with self.assertRaises(ValueError): inspect(data)
