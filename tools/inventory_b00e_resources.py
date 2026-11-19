import sys,hashlib,json,struct,collections,argparse
from pathlib import Path
from extract_someip_pcap import extract
p=argparse.ArgumentParser(description='Offline B00E resource inventory; output contains private payloads.')
p.add_argument('root',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
seen=set();rows=[];errors=[]
for p in args.root.rglob('*.pcap'):
 if p.stat().st_size>64*1024*1024:continue
 b=p.read_bytes();sha=hashlib.sha256(b).hexdigest()
 if sha in seen:continue
 seen.add(sha)
 try:streams=extract(b,max_bytes=64*1024*1024,max_packets=65536)['streams']
 except ValueError as e:errors.append({'path':str(p),'error':str(e)});continue
 for s in streams:
  if s['parse_error']:continue
  off=0;raw=s['data']
  while off<len(raw):
   n=struct.unpack_from('>I',raw,off+4)[0]+8;pkt=raw[off:off+n];off+=n
   if pkt[:4]!=bytes.fromhex('b00e0003') or pkt[14]!=0:continue
   body=pkt[16:]
   if len(body)<22:raise ValueError('short resource')
   handle,rid,typ,size,variant=struct.unpack_from('>IIBII',body)
   if len(body)!=17+size or body[4:9]!=body[17:22]:raise ValueError('resource envelope')
   rows.append({'path':str(p),'pcap_sha256':sha,'flow':s['flow'],'handle':handle,'resource_id':rid,'type':typ,'variant':variant,'bytes':len(body),'body_hex':body.hex()})
r={'unique_pcaps':len(seen),'resources':rows,'errors':errors};args.output.write_text(json.dumps(r,indent=2));print('captures',len(seen),'resource writes',len(rows),'types',collections.Counter((x['type'],x['variant']) for x in rows),'errors',len(errors))
