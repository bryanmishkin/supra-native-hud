#!/usr/bin/env python3
"""Inspect a retained RIC create reply offline. Never transmits or enables drawing."""
import argparse,hashlib,json,struct
from pathlib import Path
from ric_lifecycle import Reader,decode_bitmap_config

def audit(packet):
 if len(packet)<24:raise ValueError('Truncated reply')
 svc,method,size,client,seq,protocol,interface,kind,code=struct.unpack('>HHIHHBBBB',packet[:16])
 if (svc,method,protocol,interface,kind,code)!=(0xb006,1,1,1,128,0) or size!=len(packet)-8:raise ValueError('Expected complete successful B006 create reply')
 r=Reader(packet[16:]);handle=r.u32();a=Reader(r.take(r.u32()));r.finish();variants=[]
 while a.pos<len(a.data):
  if len(variants)>=256:raise ValueError('Too many variants')
  n,tag=a.u32(),a.u32();raw=a.take(n);row={'tag':tag,'bytes':n,'sha256':hashlib.sha256(raw).hexdigest()}
  if tag==33:
   row['bitmap']=decode_bitmap_config(raw);row['bitmap']['wire_format']='Observed in this saved create reply; field decoder statically traced'
  elif tag==35:
   if n!=16:raise ValueError('Expected 16-byte picture-in-picture configuration')
   kind,resource,count,offset,x,y,depth,packing=struct.unpack('>BBIIHHBB',raw)
   if kind!=35 or resource>11 or depth>1 or packing==3:raise ValueError('Invalid picture-in-picture configuration')
   row['picture_in_picture']={'configuration_kind':kind,'resource_type':resource,'resource_element_count':count,'resource_element_offset':offset,'maximum_resolution_pair':[x,y],'supported_color_depth_enum':depth,'supported_packaging_raw':packing}
   row['limit']='Static-decoded configuration; pixel source, ownership and HUD binding unproven; not a bitmap size allowance'
  elif tag==30 and n==20:
   row['untraced_u16_pair_at_offset_16']=list(struct.unpack_from('>HH',raw,16))
   row['limit']='Road-model configuration tail; do not treat as a writable placement control'
  variants.append(row)
 return {'reply_sha256':hashlib.sha256(packet).hexdigest(),'handle':handle,'variants':variants,'live_test_ready':False,'larger_windshield_surface_proven':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('reply',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();v=audit(a.reply.read_bytes());a.output.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v[k] for k in ['reply_sha256','handle','live_test_ready','larger_windshield_surface_proven']}))
