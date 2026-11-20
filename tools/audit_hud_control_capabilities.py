#!/usr/bin/env python3
"""Offline B006 capability/model inventory for types30/50. No vehicle I/O."""
import argparse,json,struct,hashlib
from pathlib import Path
from extract_someip_pcap import extract

def audit(root):
    captures=[]
    for path in sorted(root.rglob('*.pcap')):
        raw=path.read_bytes();r={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'create_replies':[],'updates':[],'errors':[]};captures.append(r)
        try: streams=extract(raw,max_bytes=64*1024*1024,max_packets=65536)['streams']
        except ValueError as e:r['errors'].append(str(e));continue
        for st in streams:
            if st['parse_error']:r['errors'].append({'flow':st['flow'],'error':st['parse_error']});continue
            d=st['data'];pos=0
            while pos<len(d):
                n=struct.unpack_from('>I',d,pos+4)[0]+8;p=d[pos:pos+n];pos+=n
                if p[:2]!=bytes.fromhex('b006'):continue
                method=struct.unpack_from('>H',p,2)[0];b=p[16:]
                if p[14]==0 and method in (9,10,11) and len(b)>=9 and b[8] in (30,50):
                    r['updates'].append({'method':method,'body_hex':b.hex()})
                if method!=1 or p[14]!=128 or p[15]!=0 or len(b)<8:continue
                length=struct.unpack_from('>I',b,4)[0]
                if length!=len(b)-8:r['errors'].append('create vector length mismatch');continue
                at=8;configs=[]
                while at<len(b):
                    if at+8>len(b):r['errors'].append('truncated config header');break
                    size,tag=struct.unpack_from('>II',b,at);at+=8
                    if at+size>len(b):r['errors'].append('truncated config body');break
                    v=b[at:at+size];at+=size
                    if len(v)>=2:configs.append({'tag':tag,'type':v[1],'payload':v.hex()})
                if at==len(b):r['create_replies'].append({'handle':struct.unpack_from('>I',b)[0],'configs':configs})
    replies=[x for c in captures for x in c['create_replies']]
    return {'captures':captures,'summary':{'create_replies':len(replies),'type30_advertised_replies':sum(any(x['type']==30 for x in r['configs']) for r in replies),'type50_advertised_replies':sum(any(x['type']==50 for x in r['configs']) for r in replies),'updates_30_or_50':sum(len(c['updates']) for c in captures)},'limitations':'Accepted classic-PCAP TCP streams only. Captures may duplicate replies. Config payloads retained; type alone does not establish drawing semantics. Decode errors remain explicit.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=audit(a.root);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']))
