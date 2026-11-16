import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_shared_trial import SharedSession,SharedDrawingTrial
from ric_owned_session import RicFailure
from ric_rle32 import encode_bgra,decode_bgra,marker_bgra

class SharedTests(unittest.TestCase):
 def test_wire_vectors(self):
  for n,hexdata in [(1,'0144332211000000'),(2,'8244332211000000'),(127,'ff44332211000000'),(128,'ff443322110144332211000000000000')]:
   raw=bytes.fromhex('11223344')*n
   self.assertEqual(encode_bgra(raw).hex(),hexdata)
   self.assertEqual(decode_bgra(bytes.fromhex(hexdata),n),raw)
 def test_marker_roundtrip(self):
  raw=marker_bgra();self.assertEqual(decode_bgra(encode_bgra(raw),150*36),raw)
 def test_no_instance_disposal_and_cleanup_order(self):
  methods=[];present=False
  def tx(p,t):
   nonlocal present
   m=struct.unpack_from('>H',p,2)[0];methods.append(m)
   if m==3:present=True
   if m==8:present=False
   b=bytes([present]) if m==2 else b''
   h=bytearray(p[:16]);h[4:8]=struct.pack('>I',8+len(b));h[14]=128
   return bytes(h)+b
  a=dict(handle=200,models={10:0x0a000004,15:0x0f000004,32:0x20000000,33:0x21000000},resource_id=0x01000009,resource_type=1,dimensions=[150,36],resource_ids=list(range(0x01000000,0x0100000a)))
  s=SharedSession(tx,a);r=SharedDrawingTrial(s,lambda r:None,lambda p,t:None).run()
  self.assertNotIn(1,methods);self.assertNotIn(7,methods)
  self.assertFalse(r['cleanup']['resources'][0]['post_dispose_check'])
  self.assertTrue(all(x['acknowledged'] for x in r['cleanup_steps']))
  self.assertEqual(methods[-2:],[8,2])
  self.assertFalse(r['visual_test_passed'])
 def test_forbidden_instance_and_untracked_resource_disposal(self):
  s=SharedSession(lambda p,t:None,{'handle':200})
  for m,b in [(1,b''),(7,struct.pack('>I',200)),(8,struct.pack('>II',200,99))]:
   with self.assertRaises(RicFailure):s._request(m,b)

class DoubleBufferAllocationTests(unittest.TestCase):
 def test_second_slot_requires_explicit_two_slot_mode(self):
  a=dict(handle=200,models={},resource_id=0x01000009,resource_ids=list(range(0x01000000,0x0100000a)))
  def tx(p,t):
   h=bytearray(p[:16]);h[4:8]=struct.pack('>I',8);h[14]=128;return bytes(h)
  normal=SharedSession(tx,a)
  with self.assertRaises(RicFailure):normal._empty(3,struct.pack('>II',200,0x01000008))
  buffered=SharedSession(tx,a,double_buffer=True)
  buffered._empty(3,struct.pack('>II',200,0x01000008))
  with self.assertRaises(RicFailure):buffered._empty(3,struct.pack('>II',200,0x01000007))
 def test_missing_second_slot_rejected(self):
  with self.assertRaises(RicFailure):SharedSession(lambda p,t:None,dict(handle=200,resource_id=5,resource_ids=[5]),double_buffer=True)
