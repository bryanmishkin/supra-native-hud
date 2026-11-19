#!/usr/bin/env python3
"""Bounded read-only receiver identity capture. Default prints plan, no sockets.
No session change, unlocking, reset, memory read, coding or firmware operation.
An explicitly supplied address is a candidate until its response identifies it.
"""
import argparse
import datetime
import hashlib
import ipaddress
import json
from pathlib import Path
import socket
import struct
import time

DIDS = (0xF197, 0xF187, 0xF189, 0xF101)
CLASSES = {1:'HWEL',2:'HWAP',4:'GWTB',5:'CAFD',6:'BTLD',8:'SWFL',13:'SWFK'}


def decode_inventory(reply):
    """Exact F101 layout validated against retained positive ECU10/12/63 replies.
    Preserve unknown class bytes; do not infer that this is cluster firmware.
    """
    if len(reply) < 20 or reply[:3] != bytes.fromhex('62f101'):
        raise ValueError('Not the retained positive F101 layout')
    if reply[3:5] != b'\x01\x01':
        raise ValueError('Unknown F101 header version; retain raw response')
    count = int.from_bytes(reply[5:7], 'big')
    if count > 256 or len(reply) != 20 + count * 8:
        raise ValueError('F101 count/length mismatch; retain raw response')
    entries = []
    for i in range(count):
        item = reply[20+i*8:28+i*8]
        entries.append(dict(class_code=item[0], category=CLASSES.get(item[0], 'unknown'),
                            id=item[1:5].hex(), version='.'.join(map(str,item[5:8]))))
    return dict(count=count, entries=entries, firmware_match_established=False)


def request_bytes(did):
    if did not in DIDS + (0x3F07,):
        raise ValueError('DID outside read-only identity allowlist')
    return b'\x22' + did.to_bytes(2,'big')


def exact(sock, count, deadline):
    result = bytearray()
    while len(result) < count:
        remaining = deadline-time.monotonic()
        if remaining <= 0: raise TimeoutError('Response deadline')
        sock.settimeout(remaining)
        part = sock.recv(count-len(result))
        if not part: raise ConnectionError('Connection closed')
        result.extend(part)
    return bytes(result)


def read_one(gateway, source, interface, ecu, did):
    req = request_bytes(did)
    row = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               ecu=f'{ecu:02x}', request=req.hex(), frames=[], status='incomplete')
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            if interface:
                # Darwin IP_BOUND_IF is IP-level 25; match the established Mac capture.
                import sys
                if sys.platform != 'darwin': raise ValueError('Interface binding supported here only on macOS')
                sock.setsockopt(socket.IPPROTO_IP,25,socket.if_nametoindex(interface))
            sock.bind((source,0)); sock.connect((gateway,6801))
            sock.sendall(struct.pack('>IHBB',len(req)+2,1,0xf4,ecu)+req)
            deadline=time.monotonic()+5
            for _ in range(64):
                length,kind=struct.unpack('>IH',exact(sock,6,deadline))
                if length>65536: raise ValueError('Oversized HSFZ frame')
                payload=exact(sock,length,deadline)
                row['frames'].append(dict(kind=kind,payload_hex=payload.hex()))
                if kind==0x12:
                    sock.sendall(struct.pack('>IHBB',2,0x13,0,0xf4))
                    continue
                if kind!=1 or payload[:2]!=bytes((ecu,0xf4)):continue
                reply=payload[2:]
                if reply==b'\x7f\x22\x78':continue
                if reply.startswith(b'\x62'+req[1:]):
                    row.update(status='positive',response_hex=reply.hex())
                    if did==0xF101:
                        try:row['inventory']=decode_inventory(reply)
                        except ValueError as e:row['decode_error']=str(e)
                    break
                if len(reply)==3 and reply[:2]==b'\x7f\x22':
                    row.update(status='negative',response_hex=reply.hex());break
            else:row['status']='frame_limit'
    except (OSError,ValueError) as e:row.update(status='error',error=str(e))
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--gateway');p.add_argument('--source-ip');p.add_argument('--interface')
    p.add_argument('--ecu',type=lambda s:int(s,16),help='Explicit candidate diagnostic address in hex; no scanning')
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    plan=dict(reads=['gateway10:223f07']+['candidate:'+request_bytes(x).hex() for x in DIDS],
              candidate_address='not selected' if a.ecu is None else f'{a.ecu:02x}',
              no_hz_tests=True,no_v1_changes=True,identity_not_yet_verified=True,
              limits='Gateway list framing is unverified on this Supra; preserve raw. No inferred cluster firmware match.')
    if not a.execute:print(json.dumps(plan,indent=2));return
    if not a.gateway or not a.source_ip or not a.output or a.ecu is None or not 1<=a.ecu<0xdf:
        p.error('Explicit gateway, source IP, output and physical ECU candidate required')
    ipaddress.IPv4Address(a.gateway);ipaddress.IPv4Address(a.source_ip)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    rows=[]
    for index,(ecu,did) in enumerate([(0x10,0x3f07)]+[(a.ecu,x) for x in DIDS]):
        row=read_one(a.gateway,a.source_ip,a.interface,ecu,did);rows.append(row)
        # Each completed query survives an interruption of subsequent queries.
        (a.output/f'{index:02d}-{ecu:02x}-{did:04x}.json').write_text(json.dumps(row,indent=2)+'\n')
        time.sleep(.25)
    result=dict(gateway=a.gateway,source=a.source_ip,interface=a.interface,queries=rows,
                receiver_match_established=False,root_geometry_established=False)
    data=(json.dumps(result,indent=2)+'\n').encode();(a.output/'capture.json').write_bytes(data)
    print(json.dumps({'saved':str(a.output),'sha256':hashlib.sha256(data).hexdigest(),
                      'positive':sum(r['status']=='positive' for r in rows),
                      'review_required':'Verify returned system name and HWEL/BTLD/SWFL before choosing receiver code.'}))

if __name__=='__main__':main()
