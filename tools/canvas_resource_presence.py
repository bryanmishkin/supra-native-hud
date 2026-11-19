#!/usr/bin/env python3
"""Check only the 5 PIP resource slots (B006 method 2, read-only).

No create, upload, initialize, graphics model update, dispose, HUD selection,
firmware command or other on-car operation. Default mode makes no connection.
Requires original saved cluster create response to derive the resource range.
A false presence reply is NOT exclusive ownership or safe drawing authorization.
"""
import argparse
import hashlib
import json
import re
import socket
import struct
import subprocess
import time
from pathlib import Path

RANGE_START=0x02000000
RANGE_COUNT=5
RANGE_TYPE=2
MAX_PACKET=1024*1024


def decode_known_profile(packet):
    if len(packet)<28 or len(packet)>MAX_PACKET:
        raise ValueError('Profile reply absent, truncated or oversized')
    svc,method,n,client,session,proto,interface,kind,code=struct.unpack_from('>HHIHHBBBB',packet,0)
    if (svc,method,proto,interface,kind,code)!=(0xb006,1,1,1,0x80,0) or n != len(packet)-8:
        raise ValueError('Expected successful saved B006 method-1 profile reply')
    body=packet[16:]
    handle,total=struct.unpack_from('>II',body)
    if handle!=200 or total!=len(body)-8:
        raise ValueError('Expected saved factory shared handle 200 with exact config extent')
    pos=8;pips=[];variants=[]
    while pos<len(body):
        if len(body)-pos<8:raise ValueError('Truncated config variant')
        length,tag=struct.unpack_from('>II',body,pos);pos+=8
        if length>len(body)-pos:raise ValueError('Invalid config variant extent')
        v=body[pos:pos+length];pos+=length;variants.append(tag)
        if tag==35:
            if len(v)!=16:raise ValueError('PIP config length mismatch')
            conf_kind,typ,count,offset,w,h,depth,pack=struct.unpack('>BBIIHHBB',v)
            if (conf_kind,typ,count,offset,w,h)!=(35,2,5,RANGE_START,320,320):
                raise ValueError('Unsupported profile: not reference Supra PiP configuration')
            pips.append(dict(type=typ,count=count,offset=offset,max_resolution=[w,h],depth=depth,packing=pack))
    if len(pips)!=1:raise ValueError('Missing or ambiguous PiP configuration')
    return dict(handle=handle,profile_sha256=hashlib.sha256(packet).hexdigest(),
                pip=pips[0],configuration_tags=variants,source='saved actual-car profile',
                not_exclusive=True)


def check_packet(resource_id,session,client=0x5350):
    if resource_id not in range(RANGE_START,RANGE_START+RANGE_COUNT):
        raise ValueError('Outside verified PIP resource range')
    body=struct.pack('>IIB',200,resource_id,RANGE_TYPE)
    return struct.pack('>HHIHHBBBB',0xb006,2,len(body)+8,client,session,1,1,0,0)+body


def verify_reply(req,reply):
    if len(reply)!=17:raise ValueError('Method-2 reply must be exactly 17 bytes')
    svc,method,n,client,session,proto,interface,kind,code=struct.unpack_from('>HHIHHBBBB',reply)
    a=struct.unpack_from('>HHIHHBBBB',req)
    if (svc,method,n,client,session,proto,interface,kind,code)!=(0xb006,2,9,a[3],a[4],1,1,0x80,0):
        raise ValueError('Unmatched, rejected or malformed resource check')
    val=reply[16]
    if val not in (0,1):raise ValueError('Missing Boolean resource presence result')
    return bool(val)


def probe(profile,exchange,record=None):
    decoded=decode_known_profile(profile)
    out=dict(schema=1,mode='read-only B006 method-2',source_profile_sha256=decoded['profile_sha256'],
             handle=200,resource_type=2,max_resolution=[320,320],
             surface_visibility_proven=False,exclusive_ownership_proven=False,
             draw_attempted=False,results=[])
    for index,rid in enumerate(range(RANGE_START,RANGE_START+RANGE_COUNT),start=1):
        req=check_packet(rid,index)
        if record:record('%02d-request.bin'%index,req)
        reply=exchange(req,2)
        if record:record('%02d-response.bin'%index,reply)
        out['results'].append(dict(resource_id=hex(rid),present=verify_reply(req,reply)))
    return out


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--profile',type=Path)
    parser.add_argument('--head');parser.add_argument('--ssh-socket',type=Path)
    parser.add_argument('--output',type=Path)
    a=parser.parse_args(argv)
    if not a.execute:
        print(json.dumps({'operation':'B006 method2, read-only only','resource_type':2,
                          'slots':[hex(RANGE_START+i) for i in range(RANGE_COUNT)],
                          'requires':'Exact saved method-1 B006 reply; operator-provided existing SSH master',
                          'creates_or_draws':False,'no_connect_without_execute':True},indent=2));return 0
    if not all((a.profile,a.head,a.ssh_socket,a.output)):
        parser.error('Requires --profile, --head, --ssh-socket, --output')
    from capture_runtime import link_local
    try:
        link_local(a.head)
        if a.output.exists():raise ValueError('Refusing to overwrite result directory')
        if not a.ssh_socket.is_file():raise ValueError('Existing SSH master socket is required')
        raw=a.profile.read_bytes();decode_known_profile(raw)
        a.output.mkdir(parents=True)
        manifest={'started_host_epoch':time.time(),'mode':'method-2 read only','forward_cleanup':False}
        def save():
            (a.output/'result.json').write_text(json.dumps(manifest,indent=2)+'\n')
        save()
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
        forward='127.0.0.1:%d:160.48.199.96:30502'%port
        base=['ssh','-S',str(a.ssh_socket.resolve())]
        dest='root@'+a.head
        fwd=subprocess.run(base+['-O','forward','-L',forward,dest],capture_output=True,timeout=10)
        if fwd.returncode:raise ValueError('SSH forwarding rejected; no resource messages sent')
        try:
            with socket.create_connection(('127.0.0.1',port),timeout=2) as sock:
                # Reuse the existing bounded, correlated V1 transport.
                from ric_live_trial import TcpExchange
                exchange=TcpExchange(sock,a.output)
                manifest.update(probe(raw,exchange))
        finally:
            cancelled=subprocess.run(base+['-O','cancel','-L',forward,dest],capture_output=True,timeout=10)
            manifest['forward_cleanup']=cancelled.returncode==0
            save()
        print(json.dumps(manifest,indent=2))
        return 0 if manifest['forward_cleanup'] else 2
    except (OSError,ValueError,subprocess.TimeoutExpired,TimeoutError) as error:
        parser.exit(2,str(error)+'\n')
if __name__=='__main__':raise SystemExit(main())

