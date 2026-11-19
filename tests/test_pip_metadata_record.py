import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from pip_metadata_record import build_record,build_cpu_upload,build_bgra_framebuffer
from pip_metadata_strip import decode_upload

class RecordTests(unittest.TestCase):
 def test_hud_and_cluster_records_differ_only_at_group_flag(self):
  cluster=build_record(4402,17,0x0f000004,True)
  hud=build_record(8402,17,0x0f000004,True)
  self.assertEqual([i for i,(a,b) in enumerate(zip(cluster,hud)) if a!=b],[7])
  self.assertEqual((cluster[7],hud[7]),(1,0))
 def test_picture_identity_and_option_have_separate_fields(self):
  r=build_record(8301,0x1234,0x0f000004,False,9)
  self.assertEqual(r[2:8],bytes.fromhex('341201090100'))
  self.assertEqual(r[16:20],bytes.fromhex('0400000f'))
  self.assertEqual(decode_upload(build_cpu_upload(8301,0x1234,0x0f000004,False,9)),r)
 def test_retired_template_matches_non_hud_but_not_hud(self):
  old=bytearray(84)
  old[0:2]=bytes.fromhex('1234');old[4]=old[7]=1
  old[16:20]=bytes.fromhex('0f000004')
  self.assertEqual(build_bgra_framebuffer(4402,0x1234,0x0f000004,True),old)
  hud=build_bgra_framebuffer(8402,0x1234,0x0f000004,True)
  self.assertEqual([i for i in range(84) if hud[i]!=old[i]],[4])
  self.assertEqual(hud[4],0)
 def test_framebuffer_identity_survives_driver_channel_permutation(self):
  framebuffer=build_bgra_framebuffer(8301,0x1234,0x0f000004,False,9)
  rgba=bytes(v for i in range(0,84,4) for v in (framebuffer[i+2],framebuffer[i+1],framebuffer[i],framebuffer[i+3]))
  self.assertEqual(rgba,build_cpu_upload(8301,0x1234,0x0f000004,False,9))
 def test_style_client_bits_not_accepted_as_type(self):
  with self.assertRaises(ValueError):build_record(0x0300206d,1,1,True)
 def test_unresolved_style_flag_rejected(self):
  with self.assertRaises(ValueError):build_record(8301,1,1,None)
 def test_picture_counter_must_be_explicit_u16(self):
  with self.assertRaises(ValueError):build_record(8301,65536,1,True)
if __name__=='__main__':unittest.main()
