#!/usr/bin/env python3
"""Run one named case from the canvas-only kit, with current admission.
No vehicle connection by default. The historical kit model is never transmitted.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from canvas_geometry import validate_size

def command(kit,case_id,port,admission,output,row=None):
 manifest=json.loads((kit/'manifest.json').read_text())
 if manifest.get('no_hz_tests') is not True:raise ValueError('Expected canvas-only kit')
 matches=[x for x in manifest['cases'] if x['case']==case_id]
 if len(matches)!=1:raise ValueError('Case absent or ambiguous')
 c=matches[0];files=[n for n in c['hashes'] if n.endswith('.bgra')]
 if len(files)!=1:raise ValueError('Expected one exact pixel fixture')
 name=files[0]
 if Path(name).name!=name:raise ValueError('Fixture must be in kit')
 asset=kit/name
 if hashlib.sha256(asset.read_bytes()).hexdigest()!=c['hashes'][name]:raise ValueError('Pixel fixture changed')
 if c['seconds']!=30:raise ValueError('Unsupported observation duration')
 validate_size(*c['size'])
 args=[sys.executable,str(Path(__file__).with_name('b00e_bitmap_trial.py')),'--execute','--port',str(port),'--admission',str(admission),'--bitmap-bgra',str(asset),'--width',str(c['size'][0]),'--height',str(c['size'][1]),'--output',str(output)]
 if c.get('model_id')==0x66:
  if type(row) is not int or row<0:raise ValueError('Entertainment requires explicit currently visible transmitted-array row')
  args+=['--row',str(row),'--column',str(c['column'])]
 else:
  if row is not None:raise ValueError('Row applies only to Entertainment')
  args+=['--content-field',str(c['content_field'])]
 return args

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kit',type=Path,required=True);p.add_argument('--case');p.add_argument('--execute',action='store_true');p.add_argument('--port',type=int);p.add_argument('--admission',type=Path);p.add_argument('--output',type=Path);p.add_argument('--row',type=int);a=p.parse_args()
 if not a.execute:
  m=json.loads((a.kit/'manifest.json').read_text());print(json.dumps({'offline':True,'no_hz_tests':m['no_hz_tests'],'cases':[x['case'] for x in m['cases']],'requires':'Current boot admission; visible result before dependent size escalation; exact cleanup after each case'},indent=2));return
 if not all([a.case,a.port,a.admission,a.output]):p.error('Execution requires case, verified forward port, current admission and new output')
 args=command(a.kit,a.case,a.port,a.admission,a.output,a.row)
 raise SystemExit(subprocess.call(args))
if __name__=='__main__':main()
