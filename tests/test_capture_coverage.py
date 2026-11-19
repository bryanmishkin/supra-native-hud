import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_saved_capture_coverage import packet_audit

def selection():
 body=struct.pack('>dHHB',1.0,460,237,1)
 return struct.pack('>HHIHHBBBB',0xb009,0x8001,len(body)+8,0,1,1,1,2,0)+body

class CoverageTests(unittest.TestCase):
 def audit(self,data,error=None):
  with patch('audit_saved_capture_coverage.extract',return_value={'packets':1,'streams':[{'flow':['a',1,'b',2],'data':data,'parse_error':error}]}):
   return packet_audit(b'fixture')
 def test_selection_decoded_without_visibility_claim(self):
  r=self.audit(selection());self.assertEqual(r['sink_events'][0]['selection'],1)
  self.assertEqual(r['services'],{'b009':1})
 def test_truncated_tail_preserves_complete_prefix(self):
  p=selection();r=self.audit(p+p[:18],f'truncated body at offset {len(p)}')
  self.assertEqual(len(r['sink_events']),1);self.assertEqual(r['validated_prefixes'][0]['bytes'],len(p))
 def test_midstream_data_not_resynchronized(self):
  r=self.audit(b'junk'+selection(),'unsupported protocol at offset 0')
  self.assertEqual(r['sink_events'],[]);self.assertEqual(len(r['excluded_streams']),1)
 def test_unknown_sink_message_retained_as_error(self):
  p=bytearray(selection());p[3]=2;r=self.audit(bytes(p))
  self.assertIn('decode_error',r['sink_events'][0])
if __name__=='__main__':unittest.main()
