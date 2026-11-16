#!/usr/bin/env python3
"""Strict offline classic-PCAP Ethernet/IPv4 TCP extraction. No network access.
Rejects truncation, IP fragmentation, gaps, conflicting overlaps and reused flows.
Does not guess message boundaries: mid-message streams remain unparsed evidence.
"""
import argparse, hashlib, json, socket, struct
from pathlib import Path
from inspect_someip_stream import inspect
MAX_BYTES=8*1024*1024

def extract(data, max_bytes=MAX_BYTES, max_packets=4096):
    if not 24<=max_bytes<=64*1024*1024 or not 1<=max_packets<=65536:raise ValueError("invalid extraction limits")
    if len(data)>max_bytes or len(data)<24: raise ValueError('invalid capture size')
    magic=data[:4]
    endian={b'\xd4\xc3\xb2\xa1':'<',b'\xa1\xb2\xc3\xd4':'>'}.get(magic)
    if not endian: raise ValueError('only classic microsecond PCAP supported')
    major,minor,zone,sig,snap,link=struct.unpack_from(endian+'HHiIII',data,4)
    if (major,minor)!=(2,4) or link!=1 or not 0<snap<=65535:raise ValueError('unsupported PCAP header')
    pos=24;groups={};syns={};packets=udp=0
    while pos<len(data):
        if len(data)-pos<16:raise ValueError('truncated record header')
        sec,usec,cap,wire=struct.unpack_from(endian+'IIII',data,pos);pos+=16
        if cap!=wire or cap>snap or usec>=1000000 or pos+cap>len(data):raise ValueError('truncated/invalid packet')
        packet=data[pos:pos+cap];pos+=cap;packets+=1
        if packets>max_packets:raise ValueError('packet count limit')
        if len(packet)<14:raise ValueError('short Ethernet frame')
        proto=struct.unpack_from('>H',packet,12)[0];off=14
        for _ in range(2):
            if proto not in (0x8100,0x88a8):break
            if len(packet)<off+4:raise ValueError('short VLAN tag')
            proto=struct.unpack_from('>H',packet,off+2)[0];off+=4
        if proto!=0x800:continue
        ip=packet[off:]
        if len(ip)<20 or ip[0]>>4!=4:raise ValueError('invalid IPv4')
        ihl=(ip[0]&15)*4;total=struct.unpack_from('>H',ip,2)[0]
        if ihl<20 or total<ihl or total>len(ip):raise ValueError('invalid IPv4 lengths')
        if struct.unpack_from('>H',ip,6)[0]&0x3fff:raise ValueError('fragmented IPv4 requires separate reassembly')
        if ip[9]==17:udp+=1;continue
        if ip[9]!=6:continue
        tcp=ip[ihl:total]
        if len(tcp)<20:raise ValueError('short TCP')
        sport,dport,seq=struct.unpack_from('>HHI',tcp)
        hlen=(tcp[12]>>4)*4
        if hlen<20 or hlen>len(tcp):raise ValueError('invalid TCP header')
        key=(socket.inet_ntoa(ip[12:16]),sport,socket.inet_ntoa(ip[16:20]),dport)
        if tcp[13]&2:
            if key in syns and syns[key]!=seq:raise ValueError('reused TCP tuple: split connections first')
            syns[key]=seq;seq=(seq+1)&0xffffffff
        body=tcp[hlen:]
        if body:groups.setdefault(key,[]).append((seq,body,sec*1000000+usec,packets))
        if len(groups)>128:raise ValueError('flow limit')
    streams=[]
    for key,parts in sorted(groups.items()):
        anchor=parts[0][0]
        relative=[(((seq-anchor+0x80000000)&0xffffffff)-0x80000000,body,ts,packet) for seq,body,ts,packet in parts]
        relative.sort(key=lambda p:p[0]);base=relative[0][0];output=bytearray()
        spans=[]
        for seq,body,ts,packet in relative:
            spans.append(dict(offset=seq-base,bytes=len(body),timestamp_us=ts,packet=packet))
            start=seq-base
            if start>len(output):raise ValueError('TCP gap in %r'%(key,))
            overlap=min(len(body),len(output)-start)
            if output[start:start+overlap]!=body[:overlap]:raise ValueError('conflicting TCP retransmission')
            output.extend(body[overlap:])
            if len(output)>max_bytes:raise ValueError('stream size limit')
        raw=bytes(output)
        try: inventory=inspect(raw);error=None
        except ValueError as e: inventory=None;error=str(e)
        streams.append(dict(flow=list(key),sha256=hashlib.sha256(raw).hexdigest(),data=raw,
                            inventory=inventory,parse_error=error,
                            boundary_proven=False,byte_spans=spans))
    return dict(packets=packets,udp_packets=udp,streams=streams,
                limitation='TCP continuity checked only inside captured interval; no checksum validation, initial message-boundary proof, ECU identity or drawing permission.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pcap',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    try:
        with a.pcap.open('rb') as f:r=extract(f.read(MAX_BYTES+1))
        a.output.mkdir(parents=True,exist_ok=False)
        for i,s in enumerate(r['streams']):
            name='stream-%03d.bin'%i;(a.output/name).write_bytes(s.pop('data'));s['file']=name
        (a.output/'inventory.json').write_text(json.dumps(r,indent=2)+'\n')
        print(json.dumps({'packets':r['packets'],'streams':len(r['streams']),'output':str(a.output)}))
    except (OSError,ValueError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':main()
