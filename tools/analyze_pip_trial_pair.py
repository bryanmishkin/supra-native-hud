#!/usr/bin/env python3
"""Correlate retained paired PiP traffic with direct transaction evidence.
No network access. Does not infer receiver code or windshield success from ACKs.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from extract_someip_pcap import extract
from audit_pip_sink import decode as sink_decode


def messages(raw):
    parsed=extract(raw,max_packets=65536)
    rows=[];errors=[]
    for stream in parsed['streams']:
        if stream['parse_error']:
            errors.append(dict(flow=stream['flow'],error=stream['parse_error']));continue
        data=stream['data'];off=0
        while off<len(data):
            n=struct.unpack_from('>I',data,off+4)[0]+8;p=data[off:off+n]
            spans=[s for s in stream['byte_spans'] if s['offset']<off+n and s['offset']+s['bytes']>off]
            row=dict(flow=stream['flow'],offset=off,first_us=min(s['timestamp_us']for s in spans),last_us=max(s['timestamp_us']for s in spans),
                     service=int.from_bytes(p[:2],'big'),method=int.from_bytes(p[2:4],'big'),client=int.from_bytes(p[8:10],'big'),session=int.from_bytes(p[10:12],'big'),kind=p[14],packet_sha256=hashlib.sha256(p).hexdigest(),packet=p)
            if row['service']==0xb009:
                try:row['sink']=sink_decode(p)
                except ValueError as e:row['sink_error']=str(e)
            rows.append(row);off+=n
    return sorted(rows,key=lambda r:r['first_us']),errors


def analyze(root,case):
    raw=(root/(case+'.pcap')).read_bytes();rows,errors=messages(raw)
    direct=[]
    for file in sorted((root/case).glob('*-request.bin')):
        packet=file.read_bytes();matches=[r for r in rows if r['packet']==packet]
        response=file.with_name(file.name.replace('-request','-response'))
        reply=response.read_bytes() if response.exists() else None
        replies=[r for r in rows if r['packet']==reply] if reply else []
        body=packet[16:];method=int.from_bytes(packet[2:4],'big')
        direct.append(dict(name=file.name,method=method,body_hex=body.hex(),request_packet_matches=len(matches),response_packet_matches=len(replies),
            first_us=min((r['first_us'] for r in matches),default=None),reply_us=min((r['last_us']for r in replies),default=None),
            model_type=body[8] if method in (9,10,11,12) and len(body)>=9 else None))
    sinks=[{k:v for k,v in r.items()if k!='packet'} for r in rows if r['service']==0xb009]
    selections=[r for r in sinks if r.get('sink',{}).get('type')=='selection']
    model_rows=[r for r in direct if r['model_type'] is not None]
    first_model=min((r['first_us']for r in model_rows if r['first_us'] is not None),default=None)
    distances=[r for r in direct if r['model_type']==29]
    report=dict(case=case,pcap_sha256=hashlib.sha256(raw).hexdigest(),direct_transactions=direct,sink_messages=sinks,stream_errors=errors,
        every_direct_transaction_seen=bool(direct) and all(r['request_packet_matches']==1 and r['response_packet_matches']==1 for r in direct),
        first_graph_us=first_model,selection_before_graph=bool(selections and first_model is not None) and all(r['last_us']<first_model for r in selections),
        selection_destinations=[r['sink']['selection']for r in selections],distance_transactions=len(distances))
    if selections and first_model is not None:report['first_graph_after_selection_ms']=(first_model-selections[0]['last_us'])/1000
    return report


def compare(a,b):
    x=a['direct_transactions'];y=b['direct_transactions']
    if len(x)!=len(y):raise ValueError('Transaction counts differ')
    diffs=[]
    for i,(left,right) in enumerate(zip(x,y)):
        if left['method']!=right['method']:raise ValueError('Method order differs')
        p=bytes.fromhex(left['body_hex']);q=bytes.fromhex(right['body_hex'])
        if len(p)!=len(q):raise ValueError('Body lengths differ')
        offsets=[j for j,(u,v) in enumerate(zip(p,q))if u!=v]
        if offsets:diffs.append(dict(transaction=i+1,method=left['method'],model_type=left['model_type'],body_offsets=offsets))
    exact=(len(diffs)==1 and diffs[0]['method']==10 and diffs[0]['model_type']==29 and set(diffs[0]['body_offsets'])<=set(range(23,31)))
    return dict(differences=diffs,only_numeric_distance_changed=exact,
        conclusion='This pair cannot identify the receiver arbitration rule. Initial selection preceding graph is temporal evidence, not proof graph updates can never cause later selection.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('session',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    cases=[analyze(a.session,c)for c in ('control461','contrast69')]
    result=dict(cases=cases,comparison=compare(*cases),vehicle_contact=False)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(cases=[{k:v for k,v in c.items()if k not in ('direct_transactions','sink_messages')}for c in cases],comparison=result['comparison']),indent=2))
