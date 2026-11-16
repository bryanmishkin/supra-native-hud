#!/usr/bin/env python3
"""Package only the reviewed symbol-free graph, from a successful parked trace."""
import argparse,struct,json,hashlib
from pathlib import Path
SETUP=[(9,33),(10,34),(10,29),(11,10),(14,40),(10,15),(12,32),(4,None),(9,33),(9,17)]
CLEAN=[(9,33),(9,33),(12,32),(11,10),(4,None),(14,40),(9,17)]
def prepare(source,dest):
 result=json.loads((source/'result.json').read_text())
 if result.get('graph_variant')!='empty-direction-zero' or result.get('live_rpm') or result.get('status')!='awaiting_visual_verification':raise ValueError('Expected verified static symbol-free trace')
 if not all(x.get('acknowledged') is True for x in result.get('cleanup_steps',[])) or len(result.get('cleanup_steps',[]))!=7:raise ValueError('Incomplete cleanup')
 rows=[]
 for index,(method,typ) in enumerate(SETUP+CLEAN,14):
  packet=(source/('%03d-request.bin'%index)).read_bytes();reply=(source/('%03d-response.bin'%index)).read_bytes()
  svc,m,n,c,q,pv,iv,k,rc=struct.unpack('>HHIHHBBBB',packet[:16]);body=packet[16:]
  if (svc,m,pv,iv,k,rc)!=(0xb006,method,1,1,0,0) or n!=len(packet)-8 or body[:4]!=struct.pack('>I',200):raise ValueError('Unexpected request')
  if typ is not None and (len(body)<17 or body[8]!=typ):raise ValueError('Unexpected model')
  if reply!=struct.pack('>HHIHHBBBB',svc,m,8,c,q,1,1,0x80,0):raise ValueError('Missing exact ACK')
  rows.append((m,body))
 if rows[3][1][9:]!=bytes(8):raise ValueError('High model not empty')
 from ric_graph import decode_graph_body
 if decode_graph_body(10,rows[5][1])['description']['maneuver_direction']!=0:raise ValueError('Direction not zero')
 blob=b'SHP1'+struct.pack('>HH',10,7)+b''.join(struct.pack('>HI',m,len(b))+b for m,b in rows)
 with dest.open('xb') as f:f.write(blob)
 dest.with_suffix('.json').write_text(json.dumps({'source':str(source),'sha256':hashlib.sha256(blob).hexdigest(),'private_measured_support_fields':True,'standalone_target_verified':False},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();prepare(a.source,a.output)
