#!/usr/bin/env python3
"""Prepare an offline content-binding/size matrix; never opens a connection.
The snapshot is an offline fixture, not admission for a future vehicle session.
"""
import argparse,hashlib,json
from pathlib import Path
from b00e_carousel import decode,replace_selected_content
import b00e_entertainment as entertainment
from ric_rle32 import marker_bgra,encode_bgra,decode_bgra
from prepare_bitmap_test_set import trident,png
from canvas_geometry import SIZES,ruler

def build(snapshot,out,entertainment_snapshot=None):
 original=snapshot.read_bytes();model=decode(original)
 out.mkdir(parents=True,exist_ok=False);rows=[]
 (out/'carousel-restore-input.bin').write_bytes(original)
 entertainment_hash=None
 for field in (1,2):
  body=replace_selected_content(original,0x01000009,field)
  for size in (36,64,96,128):
   for kind in ('cross','iu-trident'):
    raw=marker_bgra(size,size) if kind=='cross' else trident(size,size)
    rle=encode_bgra(raw)
    if decode_bgra(rle,size*size)!=raw:raise ValueError('Pixel encoding differs')
    name=f'content-{field}-{size}x{size}-{kind}'
    files={}
    for ext,data in [('bgra',raw),('rle32',rle),('png',png(raw,size,size)),('model.bin',body)]:
     fn=name+'.'+ext;(out/fn).write_bytes(data);files[fn]=hashlib.sha256(data).hexdigest()
    rows.append(dict(case=name,content_field=field,size=[size,size],seconds=30,hashes=files,
      prerequisite='Correct distinct pixels at 36x36 before size ladder; exact restoration and removal after every case',
      live_admitted=False))
 if entertainment_snapshot is not None:
  ent=entertainment_snapshot.read_bytes();parsed=entertainment.decode(ent)
  entertainment_hash=hashlib.sha256(ent).hexdigest()
  (out/'entertainment-restore-input.bin').write_bytes(ent)
  for column in (1,2):
   body=entertainment.replace_content_cell(ent,0x01000009,0,column)
   for size in (36,64,96,128):
    for kind in ('cross','iu-trident'):
     raw=marker_bgra(size,size) if kind=='cross' else trident(size,size);rle=encode_bgra(raw)
     if decode_bgra(rle,size*size)!=raw:raise ValueError('Pixel encoding differs')
     name=f'entertainment-row0-column{column}-{size}x{size}-{kind}';files={}
     for ext,data in [('bgra',raw),('rle32',rle),('png',png(raw,size,size)),('model.bin',body)]:
      fn=name+'.'+ext;(out/fn).write_bytes(data);files[fn]=hashlib.sha256(data).hexdigest()
     rows.append(dict(case=name,model_id=0x66,row=0,column=column,size=[size,size],seconds=30,hashes=files,live_admitted=False,
      prerequisite='Current full Entertainment snapshot and visibly identified row; offline row0 is not a selection assertion'))
 # Add geometry rulers for each distinct evidenced binding. Rectangular pairs
 # separate aspect-ratio behavior from simple square-image acceptance.
 templates=[r for r in rows if r['case'].endswith('36x36-cross')]
 for template in templates:
  prefix=template['case'].rsplit('36x36-cross',1)[0]
  body=(out/next(n for n in template['hashes'] if n.endswith('.model.bin'))).read_bytes()
  for width,height in SIZES:
   raw=ruler(width,height);rle=encode_bgra(raw)
   if decode_bgra(rle,width*height)!=raw:raise ValueError('Ruler encoding differs')
   name=f'{prefix}{width}x{height}-ruler';files={}
   for ext,data in [('bgra',raw),('rle32',rle),('png',png(raw,width,height)),('model.bin',body)]:
    fn=name+'.'+ext;(out/fn).write_bytes(data);files[fn]=hashlib.sha256(data).hexdigest()
   row={k:v for k,v in template.items() if k not in ('case','size','hashes','prerequisite')}
   row.update(case=name,size=[width,height],hashes=files,
    prerequisite='Distinct 36x36 content image first; size/aspect cases conditional on verified cleanup and visible binding')
   rows.append(row)
 result=dict(schema=1,scope='Offline fixtures only; no vehicle connection or V1 changes',
  snapshot_sha256=hashlib.sha256(original).hexdigest(),entertainment_snapshot_sha256=entertainment_hash,selected_index=model['index'],
  binding='Only one selected content cell replaced; icon/other cells/items/flags unchanged',
  no_hz_tests=True,visual_geometry_verified=False,cases=rows,
  geometry_edges={'top':'cyan','bottom':'orange','left':'green','right':'magenta','tick_spacing_source_pixels':8},
  run_order=['Known B006 control only if observation pipeline needs checking',
   'Content1 36 cross then IU; content2 36 cross then IU',
   'Entertainment content columns1/2 at explicit visible row; first distinct36x36 markers',
   'For each visually working content cell: 64,96,128; stop size escalation on clipping/rejection',
   'Restore V1 and verify baseline, worker and advancing RPM'],
  admission='Refresh same-boot factory model/idle focus and verify clean V1 pause before any live command')
 (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--entertainment-snapshot',type=Path);a=p.parse_args()
 print(json.dumps(build(a.snapshot,a.output,a.entertainment_snapshot),indent=2))
