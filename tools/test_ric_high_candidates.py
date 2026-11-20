import unittest
import ric_branch_high as branch
import ric_tunnel_high as tunnel
import ric_destination_high as destination

class Codecs(unittest.TestCase):
 def test_branch_roundtrip(self):
  for picture in (0x1000008,0x1000009,0xffffffff):
   b=branch.encode(200,0x3000004,3,3,picture)
   self.assertEqual(branch.encode(**branch.decode(b)),b)
 def test_tunnel_roundtrip(self):
  for text in ('','125','é'):
   for picture in (0x1000008,0xffffffff):
    b=tunnel.encode(200,0xd000004,13,4,125.5,text,0,picture)
    self.assertEqual(tunnel.encode(**tunnel.decode(b)),b)
 def test_branch_malformed(self):
  good=branch.encode(200,0x3000004,3,3,0xffffffff)
  for b in (good[:-1],good+b'\0',good[:8]+b'\x08'+good[9:],good[:16]+b'\x08'+good[17:]):
   with self.assertRaises(ValueError):branch.decode(b)
 def test_tunnel_malformed(self):
  good=tunnel.encode(200,0xd000004,13,4,125.5,'125',0,0xffffffff)
  for b in (good[:-1],good+b'\0',good[:8]+b'\x03'+good[9:],good[:35]+b'\0\0'+good[37:]):
   with self.assertRaises(ValueError):tunnel.decode(b)
 def test_destination_factory_and_absence(self):
  raw=bytes.fromhex("000000c831000000310000000c0000000a3100000031000000ffffffff")
  self.assertEqual(destination.encode(**destination.decode(raw)),raw)
  for picture in (0x1000008,0x1000009,0xffffffff):
   b=destination.encode(200,0x31000000,49,0,0,picture)
   self.assertEqual(destination.encode(**destination.decode(b)),b)
  for bad in (raw[:-1],raw+b"x",raw[:8]+b"\x03"+raw[9:]):
   with self.assertRaises(ValueError):destination.decode(bad)
  with self.assertRaises(ValueError):destination.encode(200,1,49,0,65536,1)
 def test_invalid_input(self):
  for t in (8,True,-1):
   with self.assertRaises(ValueError):branch.encode(200,1,t,3,1)
  for n in (float('inf'),float('nan'),-1,True):
   with self.assertRaises(ValueError):tunnel.encode(200,1,13,4,n,'',0,1)
  with self.assertRaises(ValueError):tunnel.encode(200,1,13,4,1,'x\0y',0,1)
  with self.assertRaises(ValueError):tunnel.encode(200,1,13,4,1,'',6,1)

if __name__=='__main__':unittest.main()
