#!/usr/bin/env python3
"""Offline B009 UDP subscription/ACK timeline. No network, no pixel proof."""
import argparse,hashlib,json,socket,struct
from pathlib import Path
from extract_someip_pcap import extract
from pip_displaysink import discovery

def audit(path):
    raw=path.read_bytes()
    # Apply the existing strict packet/fragment/truncation bounds before decoding UDP.
    extract(raw,max_bytes=64*1024*1024,max_packets=65536)
    endian='<' if raw[:4]==b'\xd4\xc3\xb2\xa1' else '>'
    pos=24;events=[];unsupported=0
    while pos<len(raw):
        sec,usec,n,wire=struct.unpack_from(endian+'IIII',raw,pos);pos+=16
        packet=raw[pos:pos+n];pos+=n;off=14;kind=struct.unpack_from('>H',packet,12)[0]
        for _ in range(2):
            if kind not in (0x8100,0x88a8):break
            kind=struct.unpack_from('>H',packet,off+2)[0];off+=4
        if kind!=0x800:continue
        ip=packet[off:];ihl=(ip[0]&15)*4;total=struct.unpack_from('>H',ip,2)[0]
        if ip[9]!=17:continue
        udp=ip[ihl:total]
        if len(udp)<8:raise ValueError('short UDP')
        sport,dport,size=struct.unpack_from('>HHH',udp)
        if not 8<=size<=len(udp):raise ValueError('invalid UDP length')
        data=udp[8:size]
        if len(data)<40 or data[:4]!=bytes.fromhex('ffff8100'):continue
        entries=struct.unpack_from('>I',data,20)[0]
        if entries%16 or 24+entries+4>len(data):raise ValueError('invalid SD entries')
        if not any(data[k+4:k+6]==bytes.fromhex('b009') for k in range(24,24+entries,16)):continue
        # Offers and bundled variants are preserved/countable, not coerced into the known codec.
        if entries!=16 or data[24] not in (6,7):unsupported+=1;continue
        row=discovery(data)
        row.update(timestamp_us=sec*1000000+usec,source=socket.inet_ntoa(ip[12:16]),
                   destination=socket.inet_ntoa(ip[16:20]),source_port=sport,destination_port=dport)
        events.append(row)
    return {'sha256':hashlib.sha256(raw).hexdigest(),'events':events,'other_b009_sd_packets':unsupported,
            'limitation':'Subscription and ACK observations only; no claim of correlation, selected destination, ownership or visible pixels.'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pcap',type=Path)
    print(json.dumps(audit(p.parse_args().pcap),indent=2))
