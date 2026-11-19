#!/usr/bin/env python3
"""Audit deduplicated saved PCAPs. Counts are observations, not independent drives.
Unparsed/excluded coverage is retained; resource uploads do not prove display.
"""
import sys,json,hashlib,struct,collections,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from extract_someip_pcap import extract
from ric_resource import decode_resource_body
from ric_rle32 import decode_bgra
parser=argparse.ArgumentParser(description='Offline capture corpus resource audit; no vehicle contact. Private output includes captured bodies.')
parser.add_argument('corpus',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
out=args.output;out.mkdir(parents=True,exist_ok=False);(out/'resources').mkdir()
seen={};captures=[];resources={};methods=collections.Counter()
for path in sorted(args.corpus.rglob('*.pcap')):
 data=path.read_bytes();sha=hashlib.sha256(data).hexdigest()
 if sha in seen:continue
 seen[sha]=str(path);cap={'path':str(path),'sha256':sha,'bytes':len(data)};captures.append(cap)
 try:a=extract(data,max_bytes=64*1024*1024,max_packets=65536)
 except ValueError as e:cap['excluded_reason']=str(e);continue
 cap['packets']=a['packets'];cap['streams']=len(a['streams']);cap['unparsed']=[]
 for s in a['streams']:
  if s['parse_error']:cap['unparsed'].append({'flow':s['flow'],'reason':s['parse_error']});continue
  b=s['data'];off=0
  while off<len(b):
   n=int.from_bytes(b[off+4:off+8],'big')+8;p=b[off:off+n];off+=n
   svc,m=struct.unpack_from('>HH',p);kind=p[14];methods[(hex(svc),m,kind)]+=1
   if svc not in (0xb006,0xb00e) or m!=3 or kind!=0:continue
   body=p[16:];h=hashlib.sha256(body).hexdigest();key=f'{svc:04x}-{h}'
   observation={'capture':str(path),'flow':s['flow'],'stream_offset':off-n,'client':int.from_bytes(p[8:10],'big'),'session':int.from_bytes(p[10:12],'big')}
   if key in resources:resources[key]['observations'].append(observation);continue
   row={'service':hex(svc),'body_sha256':h,'observations':[observation]};resources[key]=row
   (out/'resources'/(key+'.bin')).write_bytes(body)
   try:
    r=decode_resource_body(body);row['decoded']=r
    if 'bitmap' in r:
     image=body[30:];w,hh=r['bitmap']['resolution_pair'];row['image_prefix']=image[:32].hex()
     try:raw=decode_bgra(image,w*hh);row['rle32']={'decoded':True,'raw_sha256':hashlib.sha256(raw).hexdigest(),'alpha_values':sorted(set(raw[3::4])),'unique_pixels':len(set(raw[i:i+4] for i in range(0,len(raw),4)))}
     except ValueError as e:row['rle32']={'decoded':False,'error':str(e)}
   except Exception as e:row['decode_error']=str(e)
report={'captures':captures,'resources':resources,'method_counts':[{'service':s,'method':m,'kind':k,'count':v} for (s,m,k),v in sorted(methods.items())]}
(out/'resource-audit.json').write_text(json.dumps(report,indent=2))
print('captures',len(captures),'excluded',sum('excluded_reason'in c for c in captures),'unique resources',len(resources))
for svc in ('0xb006','0xb00e'):
 rows=[r for r in resources.values() if r['service']==svc];print(svc,'unique',len(rows),'types',collections.Counter((r.get('decoded',{}).get('resource_type'),r.get('decoded',{}).get('variant_tag')) for r in rows))
 print('bitmap samples',[(r['decoded']['bitmap']['resolution_pair'],r['decoded']['bitmap']['image_bytes'],r.get('image_prefix'),r.get('rle32')) for r in rows if 'bitmap'in r.get('decoded',{})][:8])
