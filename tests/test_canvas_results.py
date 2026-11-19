import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from summarize_canvas_results import summarize
class ResultsTests(unittest.TestCase):
 def test_acknowledgment_never_counts_as_visible_canvas(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);case=root/'case';case.mkdir()
   result={'protocol_cleanup_ok':True,'cleanup':[{'ok':True}],'model_id':109,'cell':{'content_field':1},'bitmap_dimensions':[128,128]}
   (case/'result.json').write_text(json.dumps(result))
   self.assertEqual(summarize(root)['verified_unclipped_windshield_bitmap_sizes'],{})
   (case/'observation.json').write_text(json.dumps({'distinct_custom_pixels':False,'all_border_edges_visible':True,'windshield':True}))
   self.assertEqual(summarize(root)['verified_unclipped_windshield_bitmap_sizes'],{})
   (case/'observation.json').write_text(json.dumps({'distinct_custom_pixels':True,'all_border_edges_visible':True,'windshield':True}))
   summary=summarize(root);self.assertEqual(list(summary['verified_unclipped_windshield_bitmap_sizes'].values()),[[[128,128]]]);self.assertIsNone(summary['root_canvas_resolution'])
   result['cleanup']=[{'ok':False}];(case/'result.json').write_text(json.dumps(result))
   self.assertEqual(summarize(root)['verified_unclipped_windshield_bitmap_sizes'],{})
if __name__=='__main__':unittest.main()
