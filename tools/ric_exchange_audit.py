#!/usr/bin/env python3
"""Correlate saved method-2 resource checks within one capture inventory.

Unique request/response IDs AND reversed endpoint tuples are required. Never
joins recording directories. Output does not establish image disappearance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from ric_resource_check import decode_check_packet


def correlate(records):
    groups={}
    for r in records:
        flow=tuple(r['flow']);d=r['decoded'];kind=d['message_type']
        if len(flow)!=4:raise ValueError('Expected four-part flow')
        oriented=flow if kind==0 else flow[2:]+flow[:2]
        key=(oriented,d['client'],d['session'])
        groups.setdefault(key,[]).append(r)
    matched=[];unresolved=[]
    for _, rows in groups.items():
        req=[r for r in rows if r['decoded']['message_type']==0]
        rep=[r for r in rows if r['decoded']['message_type']!=0]
        if len(req)!=1 or len(rep)!=1:
            unresolved.append({'reason':'nonunique or missing request/response','records':rows});continue
        q,a=req[0],rep[0]
        if q.get('timestamp_us') is None or a.get('timestamp_us') is None or a['timestamp_us'] < q['timestamp_us']:
            unresolved.append({'reason':'missing or inconsistent timing','records':rows});continue
        matched.append({'request':q,'response':a,'check_result':a['decoded'].get('check_result'),
                        'remote_cleanup_proven':False})
    return {'matched':matched,'unresolved':unresolved,'remote_cleanup_proven':False}


def audit_inventory(path):
    path=Path(path);root=path.parent.resolve();inventory=json.loads(path.read_text());records=[]
    for stream in inventory['streams']:
        if stream.get('parse_error'):continue
        file=(root/stream['file']).resolve()
        if file.parent!=root:raise ValueError('Stream path escapes recording directory')
        data=file.read_bytes()
        if hashlib.sha256(data).hexdigest()!=stream['sha256']:
            raise ValueError('Stream hash mismatch')
        offset=0
        while offset<len(data):
            if len(data)-offset<16:raise ValueError('Truncated stream header')
            svc,method,n=struct.unpack_from('>HHI',data,offset);end=offset+n+8
            if n<8 or end>len(data):raise ValueError('Invalid stream extent')
            if svc==0xb006 and method==2:
                times=[s['timestamp_us'] for s in stream.get('byte_spans',[]) if s['offset']<=offset<s['offset']+s['bytes']]
                records.append({'file':file.name,'offset':offset,'flow':stream['flow'],
                    'timestamp_us':times[0] if len(times)==1 else None,
                    'boundary_proven':stream.get('boundary_proven',False),
                    'decoded':decode_check_packet(data[offset:end])})
            offset=end
    result=correlate(records)
    result['limitation']='Unique matches within one saved recording; no complete TCP epoch, resource ownership or visual-erasure proof.'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('inventory',type=Path);a=p.parse_args()
    try:print(json.dumps(audit_inventory(a.inventory),indent=2))
    except (ValueError,OSError,KeyError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':main()
