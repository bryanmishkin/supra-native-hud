#!/usr/bin/env python3
"""Read-only inventory of retained captures, archive members and fault records."""
import argparse, collections, hashlib, json, re, zipfile
from pathlib import Path
from extract_someip_pcap import extract
from inspect_someip_stream import inspect
from audit_pip_sink import decode

def packet_audit(raw):
    parsed=extract(raw,max_bytes=64*1024*1024,max_packets=65536)
    events=[]; excluded=[]; services=collections.Counter(); prefixes=[]
    for s in parsed['streams']:
        data=s['data']
        if s['parse_error']:
            m=re.fullmatch(r'truncated (?:body|header) at offset (\d+)',s['parse_error'])
            if not m:
                excluded.append({'flow':s['flow'],'reason':s['parse_error']});continue
            data=data[:int(m[1])];prefixes.append({'flow':s['flow'],'bytes':len(data)})
        inspect(data)
        at=0
        while at<len(data):
            n=int.from_bytes(data[at+4:at+8],'big')+8;p=data[at:at+n]
            services[p[:2].hex()]+=1
            if p[:2]==b'\xb0\x09':
                try: row=decode(p)
                except ValueError as e:row={'decode_error':str(e),'hex':p.hex()}
                row.update(flow=s['flow'],offset=at);events.append(row)
            at+=n
    return {'packets':parsed['packets'],'services':dict(services),'sink_events':events,
            'excluded_streams':excluded,'validated_prefixes':prefixes}

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('root',type=Path);a.add_argument('output',type=Path);args=a.parse_args()
    captures={};faults={};archives=[];errors=[]
    def capture(raw,source):
        h=hashlib.sha256(raw).hexdigest()
        if h not in captures:
            try: result=packet_audit(raw)
            except ValueError as e:result={'excluded_reason':str(e)}
            captures[h]={'sources':[],'bytes':len(raw),**result}
        captures[h]['sources'].append(source)
    for p in sorted(args.root.rglob('*.pcap')):capture(p.read_bytes(),str(p))
    loose_hashes=set(captures)
    for p in sorted(args.root.rglob('*.zip')):
        try:
            with zipfile.ZipFile(p) as z:
                members=[x for x in z.infolist() if x.filename.endswith('.pcap')]
                archives.append({'path':str(p),'pcap_members':len(members)})
                for m in members:
                    if m.file_size>64*1024*1024:
                        errors.append({'source':str(p)+'!'+m.filename,'reason':'over 64MiB bound'});continue
                    capture(z.read(m),str(p)+'!'+m.filename)
        except (OSError,ValueError,zipfile.BadZipFile) as e:errors.append({'source':str(p),'reason':str(e)})
    for p in sorted(args.root.rglob('*fault*.json')):
        try:
            raw=p.read_bytes();d=json.loads(raw)
            if not isinstance(d,dict) or not ('event' in d and 'fault' in d):continue
            h=hashlib.sha256(raw).hexdigest()
            if h not in faults:
                result=d.get('worker.result',{})
                if isinstance(result,str):
                    try:result=json.loads(result)
                    except ValueError:result={'unparsed':True}
                faults[h]={'sources':[],'event':d.get('event'),'fault':d.get('fault'),
                    'wall_epoch':d.get('wall_epoch'),'monotonic_ms':d.get('monotonic_ms'),
                    'cleanup_proven':d.get('cleanup_proven'),'worker_result':result}
            faults[h]['sources'].append(str(p))
        except (OSError,ValueError):continue
    summary={'loose_unique_pcaps':len(loose_hashes),'all_unique_pcaps':len(captures),
        'archive_only_hashes':sorted(set(captures)-loose_hashes),'archive_count':len(archives),
        'unique_fault_records':len(faults),'fault_counts':dict(collections.Counter(str(x['fault']) for x in faults.values())),
        'sink_tuples':dict(collections.Counter(str((e.get('scale'),e.get('width'),e.get('height'),e.get('selection'))) for c in captures.values() for e in c.get('sink_events',[]) if e.get('type')=='selection'))}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'summary':summary,'captures':captures,'faults':faults,'archives':archives,'errors':errors,
        'limitations':['Content-hash deduplication is not event deduplication.','This is local retained data and first-level decoding, not proof every firmware or video has been analyzed.','Fault records from different installed builds are not current-build failures by default.','B009 selections do not prove attached pixels.']},indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
