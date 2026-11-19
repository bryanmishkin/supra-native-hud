#!/usr/bin/env python3
"""Offline catalog of captured selected view definitions. Never contacts a car."""
import argparse,hashlib,json,re
from pathlib import Path
from style_xpd import Xpd,xar_entries,guiding_view_keys,hash_component,FormatError

def pair(word):
 return [v-65536 if v>=32768 else v for v in (word&65535,word>>16)]
def catalog(root):
 manifest=json.loads((root/'manifest.json').read_text());ids={};files=[]
 for remote,row in manifest['files'].items():
  if row.get('status') not in ('verified','reverified'):continue
  path=(root/row['file']).resolve()
  if not path.is_relative_to(root.resolve()):raise FormatError('Capture file escapes root')
  data=path.read_bytes()
  if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise FormatError('Capture size/hash mismatch')
  if remote.endswith('.hpp'):
   for name,value in re.findall(r'^\s*#define\s+(VIEW_\w+)\s+([0-9]+)',data.decode('latin1'),re.M):ids.setdefault(int(value),[]).append(name)
  if remote.endswith('.xar'):files.append((remote,data))
 image_properties={}
 for remote,data in files:
  if not remote.endswith('ImageProperty.xar'):continue
  for ent in xar_entries(data):
   if ent['kind']=='XPD':image_properties[remote]=Xpd(data,ent['offset'])
 result=[]
 for remote,data in files:
  for ent in xar_entries(data):
   if ent['kind']!='XPD':continue
   db=Xpd(data,ent['offset'])
   for ident,names in sorted(ids.items()):
    node=db.lookup_hashes(guiding_view_keys(ident))
    if node is None:continue
    try:
     definition=db.view_definition(node)
    except FormatError as e:
     result.append({'file':Path(remote).name,'view':ident,'names':names,'error':str(e)});continue
    elements=[]
    for words in definition['elements']:
     xy0,xy1=pair(words[0]),pair(words[1]);elements.append({'rectangle_i16':xy0+xy1,'extent_from_endpoints':[xy1[0]-xy0[0],xy1[1]-xy0[1]],'renderer_type':words[2],'flags_word':words[3],'style_or_resource_id':words[4],'raw_words':words})
    for element in elements:
     ref=element['style_or_resource_id'];element['linked_properties']={}
     for prop in ['box','renderContainer','izStyle','junctionView','symbols','backgroundBitmap','arrowBitmap']:
      hit=db.lookup_hashes([hash_component('guiding'),hash_component('styleRef'+str(ref)),hash_component(prop)])
      if hit is not None and db.node(hit)['type']==3:element['linked_properties'][prop]=db.int32_array(hit)
     if element['renderer_type']==3:
      element['image_attributes']=[]
      for image_file,image_db in image_properties.items():
       hit=image_db.lookup_hashes([hash_component('bitmapID'),hash_component('attr'),hash_component(str(ref))])
       if hit is not None:element['image_attributes'].append({'file':Path(image_file).name,'words':image_db.int32_array(hit)})
    result.append({'file':Path(remote).name,'sha256' :hashlib.sha256(data).hexdigest(),'view':ident,'names':names,'node_offset':node,'header_words':definition['header'],'header_i16_pairs':[pair(x) for x in definition['header'][:2]],'elements':elements,'trailing_words':definition['trailing_words']})
 return {'schema':1,'views':result,'limits':'Signed coordinate pairs follow native element geometry. Header pair semantics and physical windshield allocation require separate tracing. No declared size is treated as an allocatable canvas.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=catalog(a.capture);a.output.write_text(json.dumps(r,indent=2)+'\n');print('Decoded',len(r['views']),'view definitions')
