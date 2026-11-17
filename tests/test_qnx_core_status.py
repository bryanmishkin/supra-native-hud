import unittest,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze_qnx_shutdown_core import status_note
class QnxCoreStatus(unittest.TestCase):
 def test_sdk_arm_status_offsets(self):
  data=bytearray(224);struct.pack_into('<II',data,0,123,7);struct.pack_into('<iiiIII',data,88,11,2,0,5,0x114d218,0xf6bfe4)
  self.assertEqual(status_note(data),{'pid':123,'tid':7,'signal':11,'signal_code':2,'fault_ip':'0x114d218','fault_address':'0xf6bfe4'})
 def test_unknown_layout_refused(self):
  with self.assertRaises(ValueError):status_note(bytes(232))
