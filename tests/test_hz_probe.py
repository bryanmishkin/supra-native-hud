import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from hz_probe import frame,run
from ric_rle32 import encode_bgra,decode_bgra
class ProbeTests(unittest.TestCase):
 def test_frame_identity_and_encoding(self):
  frames=[frame(n) for n in [0,1,2,10,12345]]
  self.assertEqual(len(set(frames)),5)
  for b in frames:
   self.assertEqual(len(b),150*36*4);self.assertEqual(decode_bgra(encode_bgra(b),5400),b)
 def test_no_catchup_burst_and_exact_duration(self):
  now=[0.];seen=[]
  def sleep(n):now[0]+=n
  def publish(n):seen.append(n);now[0]+=.01;return now[0]
  rows=run(10,30,publish,lambda r:None,lambda:now[0],sleep)
  self.assertEqual(seen,list(range(1,301)));self.assertEqual(now[0],30.)
  self.assertTrue(all(not r['missed_period'] for r in rows))
 def test_slow_cycle_stops_escalation(self):
  now=[0.];rows=[]
  def publish(n):now[0]+=.11;return now[0]
  with self.assertRaises(RuntimeError):run(10,30,publish,lambda r:rows.extend(r),lambda:now[0],lambda n:None)
  self.assertEqual(len(rows),1);self.assertTrue(rows[0]['missed_period'])
if __name__=='__main__':unittest.main()
