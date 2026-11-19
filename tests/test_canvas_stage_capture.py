import importlib.util, tempfile, unittest, pathlib, subprocess
from types import SimpleNamespace
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('canvas',ROOT/'tools'/'canvas_stage_capture.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
spec2=importlib.util.spec_from_file_location('diff',ROOT/'tools'/'canvas_stage_diff.py')
d=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(d)

class Tests(unittest.TestCase):
    def test_dry_run(self):
        self.assertEqual(c.main([]),0)
    def test_listing_filters(self):
        s='nrwxrwxrwx 3 root root 5132 Nov 16 19:14 GVCommand_9_1_5132\n'+\
          'nrwxrwxrwx 3 root root 120 Nov 16 19:14 SomethingElse\n'+\
          'nrwxrwxrwx 3 root root 5132 Nov 16 19:14 GVCommand_5_1_6000\n'
        r=c.parse_listing(s);self.assertEqual(len(r),1);self.assertEqual(r[0]['displayable_id'],9)
    def test_pip_summary(self):
        import struct
        raw=struct.pack('<IIIII',0,0,0xfffffffe,0x70008,12)+bytes.fromhex('00022003e001000102000000')+bytes(5100)
        o=c.summarize_gv(raw)
        self.assertTrue(o['reusable']);self.assertEqual(o['pip_words_le16'],[512,800,480,256]);self.assertFalse(o['pip_geometry_verified'])
    def test_readonly_stage_with_fixture(self):
        import struct
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td);known=root/'known';known.write_text('hostkey')
            args=SimpleNamespace(output=root/'out',known_hosts=known,stage='hud-height-top',note='operator saw rectangle',
                                 samples=2,interval_ms=0)
            calls=[];payload=struct.pack('<IIIII',0,0,0xfffffffe,0x70008,12)+bytes.fromhex('00022003e001000102000000')+bytes(5100)
            def fixture(cmd,_):
                calls.append(cmd)
                if cmd=='uname -a': data=b'QNX hu-omap 6.5 armle'
                elif cmd=='ls -l /opt/nav/eceusa/bin':data=b'nrwxrwxrwx 3 root root 5132 Nov 16 19:14 GVCommand_9_1_5132\n'
                elif cmd.startswith('dd if=/opt/nav/'):data=payload
                else:data=b'ok'
                return subprocess.CompletedProcess([],0,data,b'')
            r=c.run(args,fixture);self.assertTrue(r['complete']);self.assertEqual(len(r['buffers']),2)
            self.assertTrue(all(x['saved'] for x in r['buffers']))
            self.assertFalse(any('rm ' in s or 'cp ' in s or 'kill ' in s for s in calls))
            with self.assertRaises(ValueError):c.run(args,fixture)
    def test_diff_flags_only_changed(self):
        a=dict(complete=True,objects_discovered=1,buffers=[dict(saved=True,displayable_id=11,name='a',sha256='1')])
        b=dict(complete=True,objects_discovered=1,buffers=[dict(saved=True,displayable_id=11,name='a',sha256='2')])
        result=d.compare([('baseline',a),('radio-open',b)])
        self.assertIn('a',result['displayables']['11']['changed_by_stage']);self.assertFalse(result['destination_proven'])
        b['complete']=False
        with self.assertRaises(ValueError):d.compare([('baseline',a),('radio-open',b)])
if __name__=='__main__':unittest.main()

