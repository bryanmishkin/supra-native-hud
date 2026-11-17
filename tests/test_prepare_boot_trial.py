import unittest,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from prepare_boot_trial import prepare,OLD,NEW
BASE=b'<DynamicConfig><ProcessTable><Process><Name>./NavNBTEvoController</Name><Partition>softrt_NAV</Partition><Args>original args</Args><ResArgs>original args</ResArgs></Process></ProcessTable><PackageTable><Package><StartEntryAction><Param>/opt/nav/eceusa/bin</Param></StartEntryAction></Package></PackageTable></DynamicConfig>'
class PrepareBoot(unittest.TestCase):
 def test_exact_single_change_and_unarmed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'source').write_bytes(BASE);m=prepare(p/'source',p/'out');self.assertEqual((p/'out/after.cfg').read_bytes().replace(NEW,OLD),BASE);self.assertFalse(m['armed']);self.assertFalse(m['draws_at_boot']);self.assertFalse((p/'out/armed').exists())
 def test_reject_changed_contract(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'source').write_bytes(BASE.replace(b'softrt_NAV',b'other'))
   with self.assertRaises(ValueError):prepare(p/'source',p/'out')
