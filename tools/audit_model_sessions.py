#!/usr/bin/env python3
"""Audit reassembled SOME/IP transactions, preserving TCP connection identity.
No network I/O, payload export, handle allocation or authorization of drawing.
"""
import argparse,json,struct
from pathlib import Path
from inspect_someip_stream import inspect
SERVICES={0xb006,0xb00e}

def audit(streams):
    pending={};responses={};handles=set();candidates=[];unknown=0;total=0;tracked=0
    for flow,data in streams:
        if len(flow)!=4:raise ValueError('Expected source/port/destination/port flow')
        inspect(data) # Framing/size/protocol validation, no resynchronization.
        total+=len(data)
        if total>32*1024*1024:raise ValueError('Aggregate stream limit exceeded')
        src=(flow[0],flow[1]);dst=(flow[2],flow[3]);pos=0
        while pos<len(data):
            svc,method,n,client,session,pv,iv,kind,rc=struct.unpack_from('>HHIHHBBBB',data,pos)
            body=data[pos+16:pos+n+8];pos+=n+8
            if svc not in SERVICES:continue
            if kind not in (0,128,129):unknown+=1;continue
            tracked+=1
            if tracked>8192:raise ValueError('Transaction message limit exceeded')
            endpoints=(src,dst) if kind==0 else (dst,src)
            key=(endpoints,svc,method,client,session,iv)
            (pending if kind==0 else responses).setdefault(key,[]).append((kind,rc,len(body)))
            if kind==0 and method==1:
                candidates.append(dict(flow=list(flow),service=svc,method=method,body_bytes=len(body),meaning='Uninterpreted method 1; not proof of allocation'))
            known=(svc==0xb006 and method in (2,3,9,14)) or (svc==0xb00e and method in (4,9,11))
            if kind==0 and known and len(body)>=4:
                handles.add((endpoints,svc,struct.unpack_from('>I',body)[0]))
    transactions=[]
    for key in sorted(set(pending)|set(responses)):
        req=pending.get(key,[]);rep=responses.get(key,[])
        status='ambiguous' if len(req)>1 or len(rep)>1 else 'missing_request' if not req else 'missing_reply' if not rep else 'ok' if rep[0][0]==128 and rep[0][1]==0 else 'rejected'
        ep,svc,method,client,session,iv=key
        transactions.append(dict(connection=[list(ep[0]),list(ep[1])],service=svc,method=method,client=client,session=session,interface=iv,requests=len(req),replies=len(rep),status=status))
    return dict(schema=1,transactions=transactions,observed_factory_handle_prefixes=[dict(connection=[list(ep[0]),list(ep[1])],service=svc,handle=h) for ep,svc,h in sorted(handles)],
                method_1_candidates=candidates,other_message_types=unknown,
                independently_owned_surface_proven=False,
                limitation='Successful replies prove protocol-level acceptance only. Method-1 meaning, initial allocation, display target, ownership, release and overlay coexistence require separate evidence. No timestamps or cross-connection ordering inferred.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);a=p.parse_args()
    try:
        inventory=a.directory/'inventory.json'
        if inventory.stat().st_size>1024*1024:raise ValueError('Inventory too large')
        info=json.loads(inventory.read_text());streams=[];loaded=0
        if len(info['streams'])>128:raise ValueError('Too many streams')
        for s in info['streams']:
            name=s['file']
            if Path(name).name!=name or name in ('.','..'):raise ValueError('Unsafe stream filename')
            path=a.directory/name
            if path.is_symlink():raise ValueError('Stream symlinks not accepted')
            with path.open('rb') as f:data=f.read(16*1024*1024+1)
            loaded+=len(data)
            if loaded>32*1024*1024:raise ValueError('Aggregate stream limit exceeded')
            streams.append((s['flow'],data))
        print(json.dumps(audit(streams),indent=2))
    except (OSError,ValueError,KeyError,TypeError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':main()
