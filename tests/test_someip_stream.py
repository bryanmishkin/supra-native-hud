import importlib.util
from pathlib import Path
import struct
import unittest

spec = importlib.util.spec_from_file_location('inspect_stream', Path(__file__).parents[1] / 'tools/inspect_someip_stream.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def frame(body=b'', length=None, protocol=1, service=0xb006):
    return struct.pack('>HHIHHBBBB', service, 10, 8+len(body) if length is None else length, 1, 2, protocol, 1, 0, 0) + body

class StreamTests(unittest.TestCase):
    def test_coalesced_messages_and_body_bounds(self):
        result = m.inspect(frame(b'ab') + frame(b'abcd') + frame(service=0x1234))
        self.assertEqual(result['messages'], 3)
        self.assertEqual(result['headers'][1]['count'], 2)
        self.assertEqual(result['headers'][1]['min_body_bytes'], 2)
        self.assertEqual(result['headers'][1]['max_body_bytes'], 4)
        self.assertFalse(result['live_drawing_authorized'])
    def test_truncation_every_offset(self):
        data = frame(b'payload')
        for end in range(1, len(data)):
            with self.subTest(end=end), self.assertRaises(ValueError): m.inspect(data[:end])
    def test_reject_bad_lengths_protocol_and_oversize(self):
        for data in (frame(length=7), frame(length=m.MAX_MESSAGE), frame(protocol=2), bytes(m.MAX_STREAM+1)):
            with self.assertRaises(ValueError): m.inspect(data)
    def test_no_silent_resynchronization(self):
        with self.assertRaises(ValueError): m.inspect(b'junk'+frame())
    def test_empty_is_not_evidence(self):
        self.assertEqual(m.inspect(b'')['messages'], 0)
        self.assertFalse(m.inspect(b'')['live_drawing_authorized'])

if __name__ == '__main__': unittest.main()
