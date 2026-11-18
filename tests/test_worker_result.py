import sys,unittest,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_v1_validation import worker_result
class WorkerResultTests(unittest.TestCase):
 def test_plain_and_native(self):
  row=json.dumps(dict(reason='duration_complete',cleanup_verified=True))
  self.assertTrue(worker_result(row)['cleanup_verified'])
  self.assertTrue(worker_result(('[DsiClient] ATTACHED to server\n'+row+'\n').encode())['cleanup_verified'])
 def test_missing_or_trailing(self):
  for value in ['','[DsiClient] ATTACHED to server\n','{}','{"reason":"x","cleanup_verified":"true"}','noise\n{"reason":"x","cleanup_verified":true}','{"reason":"x","cleanup_verified":true}\ntrailing']:
   with self.assertRaises(ValueError):worker_result(value)
if __name__=='__main__':unittest.main()
