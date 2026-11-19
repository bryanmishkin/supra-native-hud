#!/usr/bin/env python3
"""Offline SOME/IP-SD advertisement inventory from saved Ethernet PCAP.

No network access, no vehicle commands, no claim that offered services are writable
HUD surfaces. Strict packet bounds and explicit malformed/unsupported counters.
"""
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

MAX_BYTES=128*1024*1024
MAX_PACKETS=65536


def parse_sd(someip):
    if len(someip)<28:raise ValueError('Short SOME/IP SD')
    svc,method,n,_,_,proto,iface,typ,code=struct.unpack_from('>HHIHHBBBB',someip)
    if (svc,method,proto,iface)!=(0xffff,0x8100,1,1) or n!=len(someip)-8:
        raise ValueError('Not a complete SOME/IP SD message')
    payload=someip[16:]
    if len(payload)<12:raise ValueError('Short SD header')
    flags=payload[0]
    if payload[1:4]!=b'\0\0\0': raise ValueError('Nonzero SD reserved bytes')
    en=struct.unpack_from('>I',payload,4)[0]
    if en%16 or en>len(payload)-12:raise ValueError('Invalid SD entry array')
    opts_at=8+en
    optlen=struct.unpack_from('>I',payload,opts_at)[0]
    if opts_at+4+optlen!=len(payload):raise ValueError('Invalid SD options extent')
    entries=[]
    for offset in range(8,opts_at,16):
        e=payload[offset:offset+16]
        entry_type=e[0]
        if entry_type not in (0,1,6,7):continue
        sid,iid=struct.unpack_from('>HH',e,4)
        major=e[8]; ttl=int.from_bytes(e[9:12],'big')
        minor=struct.unpack_from('>I',e,12)[0]
        entries.append(dict(kind={0:'find',1:'offer',6:'subscribe',7:'subscribe_ack'}[entry_type],
                            service_id=hex(sid),instance_id=hex(iid),major=major,
                            minor=minor,ttl=ttl,first_option_index=e[1],
                            second_option_index=e[2], option_counts=[e[3]>>4,e[3]&15]))
    opts=[];at=opts_at+4
    while at<len(payload):
        if at+3>len(payload):raise ValueError('Truncated SD option')
        length=struct.unpack_from('>H',payload,at)[0]
        if length<1 or at+3+length>len(payload):raise ValueError('Invalid SD option length')
        kind=payload[at+2];opt=dict(type=hex(kind),bytes=length+3)
        # IPv4 Endpoint option: reserved, IPv4, reserved, L4 protocol, port.
        if kind in (0x04,0x14) and length==9:
            b=payload[at+3:at+3+length]
            if len(b)==9:
                opt.update(address='.'.join(str(x) for x in b[1:5]),transport=b[6],port=struct.unpack_from('>H',b,7)[0])
        opts.append(opt);at+=3+length
    return dict(flags=flags,entries=entries,options=opts,message_type=typ,return_code=code)


def pcap_inventory(raw):
    if not 24<=len(raw)<=MAX_BYTES:raise ValueError('PCAP size outside bounds')
    magic=raw[:4]
    if magic==b'\xd4\xc3\xb2\xa1':endian='<'
    elif magic==b'\xa1\xb2\xc3\xd4':endian='>'
    elif magic==b'\x4d\x3c\xb2\xa1':endian='<'
    elif magic==b'\xa1\xb2\x3c\x4d':endian='>'
    else:raise ValueError('Expected classic PCAP')
    if struct.unpack_from(endian+'I',raw,20)[0]!=1:raise ValueError('Expected Ethernet PCAP')
    pos=24;packets=0;sd_packets=0;malformed=0;services=Counter();offer_endpoints={};examples={}
    while pos<len(raw):
        if len(raw)-pos<16:raise ValueError('Truncated PCAP packet header')
        _,_,captured,original=struct.unpack_from(endian+'IIII',raw,pos);pos+=16
        if captured>65535 or original<captured or pos+captured>len(raw):raise ValueError('Invalid PCAP packet size')
        b=raw[pos:pos+captured];pos+=captured;packets+=1
        if packets>MAX_PACKETS:raise ValueError('PCAP packet count exceeded')
        if len(b)<34:continue
        ether=struct.unpack_from('>H',b,12)[0];ip=14
        if ether==0x8100 and len(b)>=38:ether=struct.unpack_from('>H',b,16)[0];ip=18
        if ether!=0x0800:continue
        if b[ip]>>4!=4:continue
        ihl=(b[ip]&0xf)*4
        if ihl<20 or len(b)<ip+ihl+8 or b[ip+9]!=17:continue
        frag=struct.unpack_from('>H',b,ip+6)[0]
        if frag&0x3fff:continue
        src='.'.join(str(x) for x in b[ip+12:ip+16]);start=ip+ihl
        sport,dport,udplen=struct.unpack_from('>HHH',b,start)
        if not (sport==30490 or dport==30490):continue
        if udplen<8 or start+udplen>len(b):malformed+=1;continue
        sd_packets+=1
        try:doc=parse_sd(b[start+8:start+udplen])
        except ValueError:malformed+=1;continue
        for e in doc['entries']:
            if e['kind'] not in ('offer','find'):continue
            key=(e['kind'],e['service_id'],e['instance_id'],src,e['major'],e['minor'])
            services[key]+=1
            examples[key]=e
            offer_endpoints[key]=doc['options']
    offers=[]
    for (kind,service,instance,src,major,minor),count in sorted(services.items()):
        offers.append(dict(kind=kind,service_id=service,instance_id=instance,source_ip=src,
                           major=major,minor=minor,count=count,
                           options_seen=offer_endpoints[(kind,service,instance,src,major,minor)],
                           endpoint_claim_proven=False))
    return dict(schema=1,sha256=hashlib.sha256(raw).hexdigest(),packets=packets,
                someip_sd_packets=sd_packets,malformed_sd=malformed,
                services=offers,service_count=len({(x['service_id'],x['instance_id']) for x in offers if x['kind']=='offer'}),
                graphics_surface_proven=False,
                note='Advertisement supports transport discovery only, not display ownership, drawable geometry or API permissions.')


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('pcap',type=Path);ap.add_argument('--output',type=Path)
    args=ap.parse_args(argv)
    try:
        with args.pcap.open('rb') as f:raw=f.read(MAX_BYTES+1)
        r=pcap_inventory(raw);data=json.dumps(r,indent=2)+'\n'
        if args.output:
            if args.output.exists():raise ValueError('Refusing to overwrite inventory')
            args.output.write_text(data)
        print(json.dumps({'pcap':str(args.pcap),'packet_count':r['packets'],
                          'sd_packets':r['someip_sd_packets'],'advertised_service_instances':r['service_count'],
                          'malformed':r['malformed_sd']},indent=2))
        return 0
    except (OSError,ValueError) as e:ap.exit(2,str(e)+'\n')
if __name__=='__main__':raise SystemExit(main())

