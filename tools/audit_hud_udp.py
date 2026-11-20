#!/usr/bin/env python3
"""Offline UDP/SOME-IP discovery audit. No live networking or drawing permission."""
import argparse,collections,hashlib,json,socket,struct
from pathlib import Path


def datagrams(data):
    if len(data)<24 or len(data)>64*1024*1024:raise ValueError('capture size')
    endian={b'\xd4\xc3\xb2\xa1':'<',b'\xa1\xb2\xc3\xd4':'>'}.get(data[:4])
    if not endian:raise ValueError('classic microsecond PCAP required')
    major,minor,_,_,snap,link=struct.unpack_from(endian+'HHiIII',data,4)
    if (major,minor,link)!=(2,4,1) or not 0<snap<=65535:raise ValueError('PCAP header')
    pos=24;number=0
    while pos<len(data):
        if len(data)-pos<16:raise ValueError('truncated record header')
        sec,usec,cap,wire=struct.unpack_from(endian+'IIII',data,pos);pos+=16;number+=1
        if number>1000000 or cap!=wire or cap>snap or usec>=1000000 or pos+cap>len(data):raise ValueError('truncated/invalid record')
        frame=data[pos:pos+cap];pos+=cap
        if len(frame)<14:raise ValueError('short Ethernet')
        typ=int.from_bytes(frame[12:14],'big');off=14
        for _ in range(2):
            if typ not in (0x8100,0x88a8):break
            if len(frame)<off+4:raise ValueError('short VLAN')
            typ=int.from_bytes(frame[off+2:off+4],'big');off+=4
        if typ!=0x800:continue
        ip=frame[off:]
        if len(ip)<20 or ip[0]>>4!=4:raise ValueError('invalid IPv4')
        ihl=(ip[0]&15)*4;total=int.from_bytes(ip[2:4],'big')
        if ihl<20 or total<ihl or total>len(ip):raise ValueError('invalid IPv4 extent')
        if ip[9]!=17:continue
        if int.from_bytes(ip[6:8],'big')&0x3fff:raise ValueError('fragmented UDP: reassembly required')
        udp=ip[ihl:total]
        if len(udp)<8:raise ValueError('short UDP')
        sport,dport,n,_=struct.unpack_from('>HHHH',udp)
        if n!=len(udp) or n<8:raise ValueError('UDP extent mismatch')
        yield dict(packet=number,time_us=sec*1000000+usec,flow=[socket.inet_ntoa(ip[12:16]),sport,socket.inet_ntoa(ip[16:20]),dport],data=udp[8:])


def messages(raw):
    rows=[];pos=0
    while pos<len(raw):
        if len(raw)-pos<16:raise ValueError('short SOME/IP header')
        s,m,n,client,session,pv,iv,kind,rc=struct.unpack_from('>HHIHHBBBB',raw,pos)
        end=pos+8+n
        if n<8 or end>len(raw) or pv!=1 or kind not in (0,1,2,0x80,0x81):raise ValueError('not complete supported SOME/IP')
        rows.append(dict(service=s,method=m,client=client,session=session,interface_version=iv,type=kind,return_code=rc,body=raw[pos+16:end]));pos=end
    if not rows:raise ValueError('empty UDP payload')
    return rows


def sd_entries(body):
    if len(body)<12:raise ValueError('short SD')
    n=int.from_bytes(body[4:8],'big');end=8+n
    if n%16 or end+4>len(body):raise ValueError('invalid SD entry extent')
    optlen=int.from_bytes(body[end:end+4],'big')
    if end+4+optlen!=len(body):raise ValueError('invalid SD options extent')
    options=[];p=end+4
    while p<len(body):
        if len(body)-p<3:raise ValueError('short SD option')
        size=int.from_bytes(body[p:p+2],'big')+3
        if size<4 or p+size>len(body):raise ValueError('SD option extent')
        option=body[p:p+size];row={'type':option[2]}
        if option[2] in (4,0x14,0x24):
            if size!=12:raise ValueError('IPv4 SD option size')
            row.update(address=socket.inet_ntoa(option[4:8]),protocol=option[9],port=int.from_bytes(option[10:12],'big'))
        options.append(row);p+=size
    rows=[]
    for p in range(8,end,16):
        e=body[p:p+16];runs=[(e[1],e[3]>>4),(e[2],e[3]&15)];selected=[]
        for start,count in runs:
            if count and start+count>len(options):raise ValueError('SD option reference')
            selected.extend(options[start:start+count])
        rows.append(dict(type=e[0],service=int.from_bytes(e[4:6],'big'),instance=int.from_bytes(e[6:8],'big'),major=e[8],ttl=int.from_bytes(e[9:12],'big'),tail=e[12:].hex(),options=selected))
    return rows


def offered_endpoints(discovery):
    """Nonzero-TTL offers, not subscriptions or inferred active services."""
    endpoints = {}
    for item in discovery:
        entry = item['entry']
        if entry['type'] != 1 or not entry['ttl']:
            continue
        for option in entry['options']:
            if option['type'] != 4 or 'address' not in option:
                continue
            key = (option['address'], option['protocol'], option['port'])
            endpoint = endpoints.setdefault(key, dict(address=key[0], protocol=key[1], port=key[2], services=set()))
            endpoint['services'].add((entry['service'], entry['instance'], entry['major']))
    return [dict(address=v['address'], protocol=v['protocol'], port=v['port'],
                 services=[dict(service=s, instance=i, major=m) for s,i,m in sorted(v['services'])])
            for _,v in sorted(endpoints.items())]


def audit(root):
    seen=set();captures=[];summary=collections.Counter();services=collections.Counter();offers={};application_flows={}
    for path in sorted(root.rglob('*.pcap')):
        raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        if sha in seen:continue
        seen.add(sha);row=dict(path=str(path),sha256=sha,udp=0,someip=0,errors=[],unknown_flows={});captures.append(row)
        try:
            for d in datagrams(raw):
                row['udp']+=1;summary['udp_datagrams']+=1
                try:ms=messages(d['data'])
                except ValueError:
                    key=str(d['flow']);v=row['unknown_flows'].setdefault(key,{'count':0,'lengths':{},'first_prefix':d['data'][:32].hex()});v['count']+=1;k=str(len(d['data']));v['lengths'][k]=v['lengths'].get(k,0)+1;continue
                row['someip']+=len(ms)
                for msg in ms:
                    key=f"{msg['service']:04x}/{msg['method']:04x}";services[key]+=1
                    if (msg['service'],msg['method']) != (0xffff,0x8100):
                        flowkey=json.dumps([d['flow'],key,msg['interface_version'],msg['type']])
                        flow=application_flows.setdefault(flowkey,dict(flow=d['flow'],service_method=key,interface_version=msg['interface_version'],message_type=msg['type'],count=0,body_lengths={},first_evidence=dict(capture_sha256=sha,packet=d['packet'],time_us=d['time_us'])))
                        flow['count']+=1
                        size=str(len(msg['body']));flow['body_lengths'][size]=flow['body_lengths'].get(size,0)+1
                    if (msg['service'],msg['method'])==(0xffff,0x8100):
                        try:
                            for e in sd_entries(msg['body']):
                                k=json.dumps(e,sort_keys=True)
                                record=offers.setdefault(k,dict(entry=e,count=0,first_evidence=dict(capture_sha256=sha,packet=d['packet'],time_us=d['time_us'],flow=d['flow'])))
                                record['count']+=1
                        except ValueError as exc:row['errors'].append({'packet':d['packet'],'error':str(exc)})
        except ValueError as exc:row['errors'].append({'capture_error':str(exc),'retained_prefix_only':True})
    return dict(captures=captures,application_flows=list(application_flows.values()),services=dict(sorted(services.items())),discovery=list(offers.values()),offered_endpoints=offered_endpoints(offers.values()),summary=dict(unique_captures=len(captures),**summary),limitations='Retained Ethernet IPv4 UDP only. No checksum validation, fragment reassembly, SD identity authentication, MOST/CAN or uncaptured traffic. Unknown payloads remain unclassified. Offers do not establish drawable surfaces.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.root);a.output.write_text(json.dumps(r,indent=2));print(json.dumps({'summary':r['summary'],'services':r['services'],'discovery_shapes':len(r['discovery']),'captures_with_errors':sum(bool(x['errors'])for x in r['captures'])},indent=2))
