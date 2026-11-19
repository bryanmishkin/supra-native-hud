import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from capture_receiver_identity import decode_inventory, request_bytes

class ReceiverIdentityTests(unittest.TestCase):
    def test_count_and_unknown_class_preserved(self):
        header=bytes.fromhex('62f10101010001')+bytes(13)
        row=bytes.fromhex('fe12345678010203')
        d=decode_inventory(header+row)
        self.assertEqual(d['entries'],[dict(class_code=254,category='unknown',id='12345678',version='1.2.3')])
        self.assertFalse(d['firmware_match_established'])
        for bad in (header+row[:-1],header+row+b'\0',b'\x7f\x22\x31'):
            with self.assertRaises(ValueError):decode_inventory(bad)
    def test_unknown_version_retains_raw_in_caller(self):
        with self.assertRaises(ValueError):decode_inventory(bytes.fromhex('62f10102010000')+bytes(13))
    def test_only_identity_reads(self):
        for did in (0xf197,0xf187,0xf189,0xf101,0x3f07):
            self.assertEqual(request_bytes(did),b'\x22'+did.to_bytes(2,'big'))
        for did in (0xf190,0x1003,0x1101,0x2701,0x2e00):
            with self.assertRaises(ValueError):request_bytes(did)

if __name__=='__main__':unittest.main()
