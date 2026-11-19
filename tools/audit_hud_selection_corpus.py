#!/usr/bin/env python3
"""Offline corpus evidence for B009 destination and B006 detailed-image models.
Never transmits, assumes receiver capability, or grants live test readiness.
"""
import argparse, hashlib, json, struct
from pathlib import Path
from extract_someip_pcap import extract
from audit_pip_sink import decode

def audit(root):
    captures=[]
    for path in sorted(root.rglob('*.pcap')):
        raw=path.read_bytes()
        row={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'events':[], 'models':[], 'errors':[]}
        captures.append(row)
        try: parsed=extract(raw,max_bytes=64*1024*1024,max_packets=65536)
        except ValueError as exc:
            row['errors'].append(str(exc)); continue
        for stream in parsed['streams']:
            if stream['parse_error']:
                row['errors'].append({'flow':stream['flow'],'error':stream['parse_error']});continue
            data=stream['data'];offset=0
            while offset<len(data):
                n=struct.unpack_from('>I',data,offset+4)[0]+8
                packet=data[offset:offset+n];offset+=n
                if packet[:2]==b'\xb0\x09':
                    try: row['events'].append(decode(packet))
                    except ValueError as exc:row['errors'].append(str(exc))
                if packet[:4]!=bytes.fromhex('b006000b') or packet[14]!=0:continue
                body=packet[16:]
                if len(body)!=71:continue
                handle,model,typ,size,variant=struct.unpack_from('>IIBII',body)
                if (typ,size,variant)!=(7,54,6):continue
                payload=body[17:]
                if struct.unpack_from('>IB',payload)!=(model,7):
                    row['errors'].append('inconsistent detailed model');continue
                normalized=bytearray(payload);normalized[:4]=b'\0'*4;normalized[18:22]=b'\0'*4
                row['models'].append({'handle':handle,'model':model,'image':struct.unpack_from('>I',payload,18)[0],
                    'payload_hex':payload.hex(),'normalized_sha256':hashlib.sha256(normalized).hexdigest()})
    return {'captures':captures,'summary':{'capture_count':len(captures),
        'selection_zero_events':sum(e.get('type')=='selection' and e['selection']==0 for c in captures for e in c['events']),
        'selection_one_events':sum(e.get('type')=='selection' and e['selection']==1 for c in captures for e in c['events']),
        'detailed_models':sum(len(c['models']) for c in captures),
        'normalized_detailed_shapes':len({m['normalized_sha256'] for c in captures for m in c['models']})},
        'limitations':'Classic PCAP TCP only; rejected captures/streams retained as errors. No absence claim for UDP, unparsed streams, uncaptured intervals, or receiver code. Normalization removes only model ID and picture reference.'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=audit(a.root);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']))
