"""Malformed/stale/foreign publication regression checks; no vehicle access."""
import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import guidance_payload as g
from guidance_bitmap import decode_owned_rgba
class OwnedPayloadTests(unittest.TestCase):
 def test_registry_pair_and_release(self):
  create=g.displayable_handshake(37,17,1,320,200)
  self.assertEqual([(x['request_type'],x['event_id'],x['sequence']) for x in create],[(0x105,0x80000004,37),(0x100,4,37)])
  release=g.displayable_release_requests(37)
  self.assertEqual([(x['request_type'],x['event_id'],x['sequence']) for x in release],[(0x106,0x80000004,37),(0x100,6,37)])
  for bad in (0,-1,True,1.5,0x100000000):
   with self.assertRaises(ValueError):g.displayable_handshake(bad,17,1,320,200)
   with self.assertRaises(ValueError):g.displayable_release_requests(bad)
 def test_snapshot_rejects_foreign_stale_and_wrong_format(self):
  meta=dict(user_id=17,maneuver_id=42,guidance_type=8301,sequence=3,byte_count=28)
  pixels=bytes(range(16));snap=b'\0'*8+struct.pack('<I',3)+pixels
  expected=dict(user_id=17,maneuver_id=42,guidance_type=8301,sequence=3,width=2,height=2)
  self.assertEqual(decode_owned_rgba(meta,snap,**expected)['pixels'],pixels)
  for key in ('user_id','maneuver_id','guidance_type','sequence','byte_count'):
   bad=dict(meta);bad[key]+=1
   with self.assertRaises(ValueError):decode_owned_rgba(bad,snap,**expected)
  for bad in (snap[:-1],snap+b'\0',snap[:8]+struct.pack('<I',0xfffffffe)+pixels):
   with self.assertRaises(ValueError):decode_owned_rgba(meta,bad,**expected)
 def test_unpadded_metadata_and_no_trailing_data(self):
  raw=struct.pack('<II',17,3)+b'own'+struct.pack('<IIII',42,8301,28,3)
  self.assertEqual(g.decode_displayable_data(raw)['guidance_type'],8301)
  for bad in (raw[:-1],raw+b'\0',raw[:8]+b'o\0n'+raw[11:]):
   with self.assertRaises(ValueError):g.decode_displayable_data(bad)
if __name__=='__main__':unittest.main()
