#!/usr/bin/env python3
"""Audit whole retained .bin files with strict SOME/IP framing, offline only."""
import argparse,collections,hashlib,json
from pathlib import Path
from inspect_someip_stream import inspect
from audit_pip_sink import decode
from ric_resource import decode_resource_packet

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 seen={}; rejected=collections.Counter(); events=[]; resources=[]; services=collections.Counter();files=0
 for path in sorted(a.root.rglob('*.bin')):
  files+=1
  if not 16<=path.stat().st_size<=8*1024*1024:rejected['size bound']+=1;continue
  raw=path.read_bytes();h=hashlib.sha256(raw).hexdigest()
  if h in seen:seen[h]['paths'].append(str(path));continue
  try:inspect(raw)
  except ValueError as e:rejected[str(e).split(' at offset')[0]]+=1;continue
  seen[h]={'paths':[str(path)],'bytes':len(raw)};at=0
  while at<len(raw):
   n=int.from_bytes(raw[at+4:at+8],'big')+8;packet=raw[at:at+n];services[packet[:2].hex()]+=1
   if packet[:2]==b'\xb0\x09':
    try:events.append({'file_sha256':h,'offset':at,**decode(packet)})
    except ValueError as e:events.append({'file_sha256':h,'offset':at,'error':str(e)})
   if packet[:4]==bytes.fromhex('b0060003') and packet[14]==0:
    try:resources.append({'file_sha256':h,'offset':at,**decode_resource_packet(packet)})
    except ValueError as e:resources.append({'file_sha256':h,'offset':at,'error':str(e)})
   at+=n
 summary={'files_considered':files,'unique_framed_files':len(seen),'service_counts':dict(services),'sink_messages':len(events),'resource_uploads':len(resources)}
 a.output.write_text(json.dumps({'summary':summary,'files':seen,'sink_events':events,'resources':resources,'rejected_counts':dict(rejected),'limitation':'Strict whole-file framing only; includes synthetic fixtures and extracted/repeated recordings. Not a count of live events, no pixel attachment inferred.'},indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
