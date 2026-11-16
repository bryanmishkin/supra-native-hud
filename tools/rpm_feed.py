#!/usr/bin/env python3
"""Bounded read-only DME OBD RPM sampler. No HUD writes or diagnostic sessions."""
import argparse,ipaddress,json,socket,struct,time
from pathlib import Path
REQUEST=bytes.fromhex('010c')
def decode_rpm(reply):
    if len(reply)!=4 or reply[:2]!=b'\x41\x0c':raise ValueError('Not an exact positive RPM reply')
    return int.from_bytes(reply[2:],'big')/4.0

def exact(sock,n,deadline,clock=time.monotonic):
    data=b''
    while len(data)<n:
        remain=deadline-clock()
        if remain<=0:raise TimeoutError('RPM response deadline')
        sock.settimeout(remain);part=sock.recv(n-len(data))
        if not part:raise ConnectionError('Gateway closed')
        data+=part
    return data

def sample(local,gateway,interface,clock=time.monotonic,timeout=.75):
    start=clock();record=dict(request='010c',ecu='12',valid=False,requested_at_ms=int(start*1000))
    try:
        with socket.socket() as s:
            s.settimeout(min(.5,timeout));s.bind((local,0))
            # Mac IP_BOUND_IF, matching the verified ENET probe. No route changes.
            s.setsockopt(socket.IPPROTO_IP,25,socket.if_nametoindex(interface))
            s.connect((gateway,6801))
            s.sendall(struct.pack('>IHBB',4,1,0xf4,0x12)+REQUEST)
            deadline=start+timeout
            for _ in range(24):
                size,kind=struct.unpack('>IH',exact(s,6,deadline,clock))
                if not 2<=size<=8192:raise ValueError('Invalid gateway frame length')
                payload=exact(s,size,deadline,clock)
                if kind==0x12:s.sendall(struct.pack('>IHBB',2,0x13,0,0xf4))
                if kind!=1 or payload[:2]!=b'\x12\xf4':continue
                body=payload[2:];record['reply']=body.hex()
                if body==b'\x7f\x01\x78':continue
                rpm=decode_rpm(body);end=clock()
                # Conservative age starts at the request, never at delayed receipt.
                record.update(rpm=rpm,sampled_at_ms=int(start*1000),received_at_ms=int(end*1000),valid=end-start<=.3)
                if not record['valid']:record['error']='Response older than 300ms'
                break
            else:raise ValueError('Gateway frame limit')
    except (OSError,ValueError) as e:record['error']=str(e)
    record['completed_at_ms']=int(clock()*1000)
    return record

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
    p.add_argument('--local');p.add_argument('--gateway',default='169.254.106.96');p.add_argument('--interface',default='en8');p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.execute:print('Plan: at most 40 read-only 010C requests, 4 Hz maximum, 10-second budget; no SSH or drawing.');return
    if not a.local or not a.output:p.error('--local and new --output required')
    for ip in (a.local,a.gateway):
        if not ipaddress.IPv4Address(ip).is_link_local:p.error('Expected ENET link-local IPv4')
    start=time.monotonic()
    with a.output.open('x') as f:
        for i in range(40):
            if time.monotonic()-start>=10:break
            before=time.monotonic();r=sample(a.local,a.gateway,a.interface);f.write(json.dumps(r)+'\n');f.flush();print(json.dumps(r),flush=True)
            time.sleep(max(0,.25-(time.monotonic()-before)))
if __name__=='__main__':main()
