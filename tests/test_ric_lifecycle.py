import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from ric_lifecycle import decode_body, decode_packet, sink_transition, decode_bitmap_config


def word(n):
    return struct.pack('>I', n)


def identity(s):
    raw = b'\xfe\xff' + s.encode('utf-16-be') + b'\0\0'
    return word(len(raw)) + raw


class LifecycleTests(unittest.TestCase):
    def test_synthetic_create_identity_and_version(self):
        body = b''.join(identity(s) for s in ['test.client', 'offline', 'test']) + word(3) + word(3) + word(1)
        result = decode_body(1, 0, 0, body)
        self.assertEqual(result['identity_strings'], ['test.client', 'offline', 'test'])
        self.assertEqual(result['version_words'], [3, 3, 1])
        self.assertFalse(result['independent_ownership_proven'])

    def test_create_response_opaque_config(self):
        config = word(3) + word(19) + b'abc' + word(0) + word(0)
        r = decode_body(1, 0x80, 0, word(1234) + word(len(config)) + config)
        self.assertEqual(r['candidate_handle'], 1234)
        self.assertEqual([x['tag'] for x in r['configuration_variants']], [19, 0])
        self.assertFalse(r['configuration_semantics_verified'])
        self.assertFalse(r['independent_ownership_proven'])

    def test_empty_config_not_permission(self):
        r = decode_body(1, 0x80, 0, word(0) + word(0))
        self.assertEqual(r['configuration_variants'], [])
        self.assertFalse(r['independent_ownership_proven'])

    def test_lifecycle_request_widths(self):
        for m in [4, 7]:
            self.assertEqual(decode_body(m, 0, 0, word(0x10203040))['handle'], 0x10203040)
        r = decode_body(8, 0, 0, word(1234) + word(5678))
        self.assertEqual(r['resource_id'], 5678)

    def test_empty_ack_is_not_visible_cleanup_proof(self):
        for m in [4, 7, 8]:
            self.assertFalse(decode_body(m, 0x80, 0, b'')['remote_cleanup_proven'])
            with self.assertRaises(ValueError): decode_body(m, 0x80, 0, b'x')

    def test_truncated_and_overrun_configs(self):
        for b in [word(1), word(1)+word(8), word(1)+word(8)+word(100)+word(1), word(1)+word(1)+b'x']:
            with self.assertRaises(ValueError): decode_body(1, 0x80, 0, b)

    def test_identity_wrong_bom_termination_and_length(self):
        for b in [word(4)+b'abcd', word(3)+b'abc', word(1026), word(4)+b'\xfe\xffab']:
            with self.assertRaises(ValueError): decode_body(1, 0, 0, b)

    def test_embedded_nul_and_nonascii_rejected(self):
        for value in ['a\0b', '\u2603']:
            with self.assertRaises(ValueError): decode_body(1, 0, 0, identity(value))

    def test_wrong_method_envelope_and_trailing(self):
        for args in [(2,0,0,b''),(7,1,0,word(1)),(7,0x81,0,b''),(7,0x80,1,b''),(7,0,0,word(1)+b'x')]:
            with self.assertRaises(ValueError): decode_body(*args)

    def test_limit_config_count(self):
        entries = (word(0)+word(1))*257
        with self.assertRaises(ValueError): decode_body(1,0x80,0,word(1)+word(len(entries))+entries)

    def test_four_routing_cases(self):
        for current in [False, True]:
            for selection in [0, 1]:
                r = sink_transition(current, selection)
                self.assertEqual(r['target'], 'hud' if selection == 0 else 'kombi')
                self.assertEqual(r['switch_required'], current != (selection == 0))
                self.assertFalse(r['drawing_allowed'])

    def test_unknown_selection_rejected(self):
        for selection in [-1, 2, True]:
            with self.assertRaises(ValueError): sink_transition(False, selection)

    def test_oversized_body_rejected(self):
        with self.assertRaises(ValueError): decode_body(1,0x80,0,b'x'*65537)

    def test_packet_identity_and_correlation_fields(self):
        p = struct.pack('>HHIHHBBBB', 0xb006, 7, 12, 12, 34, 1, 1, 0, 0) + word(1234)
        r = decode_packet(p)
        self.assertEqual((r['client'], r['session'], r['handle']), (12, 34, 1234))
        self.assertFalse(r['independent_ownership_proven'])

    def test_other_service_not_misclassified(self):
        p = struct.pack('>HHIHHBBBB', 0xb00e, 4, 12, 12, 34, 1, 1, 0, 0) + word(1234)
        with self.assertRaises(ValueError): decode_packet(p)

    def test_packet_length_and_version_rejected(self):
        for length, protocol, interface in [(8,1,1),(12,2,1),(12,1,2)]:
            p = struct.pack('>HHIHHBBBB', 0xb006, 7, length, 12, 34, protocol, interface, 0, 0) + word(1234)
            with self.assertRaises(ValueError): decode_packet(p)


class BitmapConfigTests(unittest.TestCase):
    def payload(self, kind=33, resource=2, flag=1):
        return struct.pack('>BBIIHHBBBB', kind, resource, 4, 100, 460, 237, flag, 0, 1, 0)

    def test_fields_and_no_ownership_inference(self):
        r = decode_bitmap_config(self.payload())
        self.assertEqual(r['resource_element_count'], 4)
        self.assertEqual(r['resource_element_offset'], 100)
        self.assertEqual(r['resolution_pair'], [460, 237])
        self.assertTrue(r['formats']['png'])
        self.assertFalse(r['drawing_allowed'])
        self.assertFalse(r['resource_ownership_proven'])

    def test_truncated_and_trailing(self):
        for raw in (self.payload()[:-1], self.payload() + b'\0'):
            with self.assertRaises(ValueError):
                decode_bitmap_config(raw)

    def test_enum_bounds(self):
        for raw in (self.payload(kind=40), self.payload(resource=12), self.payload(flag=2)):
            with self.assertRaises(ValueError):
                decode_bitmap_config(raw)
