#!/usr/bin/env python3
"""Replay saved PCAPs through the exact native packet classifier; no network."""
import ctypes,struct,json,argparse
from pathlib import Path

def audit(lib,path):
 b=path.read_bytes();endian={b'\xd4\xc3\xb2\xa1':'<',b'\xa1\xb2\xc3\xd4':'>'}.get(b[:4])
 if not endian or len(b)<24 or struct.unpack_from(endian+'I',b,20)[0]!=1:raise ValueError('Expected Ethernet PCAP')
 at=24;counts=[0,0,0,0];first=None;last=None
 while at<len(b):
  sec,usec,cap,wire=struct.unpack_from(endian+'IIII',b,at);at+=16;p=b[at:at+cap];at+=cap
  if len(p)!=cap:raise ValueError('Truncated capture')
  data=(ctypes.c_ubyte*len(p)).from_buffer_copy(p);kind=lib.classify(data,len(p),wire,0x7f000001,65535,0xa030c760);counts[kind]+=1
  if kind==2:
   if first is None:first=sec+usec/1e6
   last=sec+usec/1e6
 return dict(path=str(path),ignored=counts[0],own=counts[1],factory_payload_packets=counts[2],unknown=counts[3],first_factory_seconds=first,last_factory_seconds=last,grants_idle_permission=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('library',type=Path);p.add_argument('output',type=Path);p.add_argument('captures',type=Path,nargs='+');a=p.parse_args();lib=ctypes.CDLL(str(a.library.resolve()));lib.classify.argtypes=[ctypes.POINTER(ctypes.c_ubyte),ctypes.c_size_t,ctypes.c_size_t,ctypes.c_uint,ctypes.c_uint,ctypes.c_uint];lib.classify.restype=ctypes.c_int
 rows=[audit(lib,f) for f in a.captures];a.output.write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
