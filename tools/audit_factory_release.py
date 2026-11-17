#!/usr/bin/env python3
"""Read saved SOME/IP streams for the statically traced release schemas; no I/O."""
import argparse,struct,json,hashlib
from pathlib import Path
def scan(root):
 rows=[]
 for path in root.rglob('stream-*.bin'):
  data=path.read_bytes();at=0
  while at+16<=len(data):
   svc,method,n,client,seq,pv,iv,kind,rc=struct.unpack_from('>HHIHHBBBB',data,at)
   if n<8 or n>65544 or at+n+8>len(data):break
   b=data[at+16:at+n+8];state=None
   if (svc,method,pv,iv,kind,rc)==(0xb00e,9,1,1,0,0) and len(b)==26 and b[:22]==bytes.fromhex('00000064000000652e0000000900000003000000652e'):
    state='radio-idle' if b[22:]==b'\xff'*4 else 'radio-active'
   if (svc,method,pv,iv,kind,rc)==(0xb006,9,1,1,0,0) and len(b)==59 and b[:22]==bytes.fromhex('000000c821000000210000002a000000022100000021') and b[30]<=8:
    state='navigation-idle' if b[30]==0 else 'navigation-active'
   if state:rows.append({'file':str(path),'offset':at,'state':state,'client':client,'session':seq,'packet_sha256':hashlib.sha256(data[at:at+n+8]).hexdigest(),'commit_ack_required':True})
   at+=n+8
 return {'observations':rows,'limitation':'Release data requires its subsequent commit acknowledgement. This inventory does not itself grant a live drawing lease.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=scan(a.root);a.output.write_text(json.dumps(r,indent=2));print(json.dumps({'observations':len(r['observations']),'idle_states':sorted(set(x['state'] for x in r['observations'] if x['state'].endswith('-idle')))}))
