import sys,struct,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rpm_feed import decode_rpm,sample
class Sock:
 def __init__(self,payload):self.data=struct.pack('>IH',len(payload),1)+payload;self.sent=[]
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def settimeout(self,t):pass
 def bind(self,a):pass
 def setsockopt(self,*a):pass
 def connect(self,a):pass
 def sendall(self,b):self.sent.append(b)
 def recv(self,n):b=self.data[:min(n,2)];self.data=self.data[len(b):];return b
class RPMTests(unittest.TestCase):
 def test_captured_values(self):
  self.assertEqual(decode_rpm(bytes.fromhex('410c0f6e')),987.5)
  self.assertEqual(decode_rpm(bytes.fromhex('410c0a44')),657)
 def test_reject_other_or_malformed_reply(self):
  for h in ['7f0111','410d1234','410c123400','410c12','']:
   with self.assertRaises(ValueError):decode_rpm(bytes.fromhex(h))
 def test_exact_read_only_request_fragmented_response(self):
  s=Sock(bytes.fromhex('12f4410c0f6e'))
  with patch('rpm_feed.socket.socket',return_value=s),patch('rpm_feed.socket.if_nametoindex',return_value=8):r=sample('169.254.1.2','169.254.1.3','en8',clock=lambda:1)
  self.assertTrue(r['valid']);self.assertEqual(r['rpm'],987.5);self.assertEqual(s.sent,[bytes.fromhex('000000040001f412010c')])
 def test_wrong_ecu_never_valid(self):
  s=Sock(bytes.fromhex('63f4410c0f6e'))
  with patch('rpm_feed.socket.socket',return_value=s),patch('rpm_feed.socket.if_nametoindex',return_value=8):r=sample('169.254.1.2','169.254.1.3','en8',clock=lambda:1)
  self.assertFalse(r['valid']);self.assertNotIn('rpm',r)
