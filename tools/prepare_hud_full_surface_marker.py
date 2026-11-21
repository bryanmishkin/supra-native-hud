#!/usr/bin/env python3
"""Build an offline 408x132 coordinate marker; no vehicle sender or resource IDs."""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
from ric_rle32 import encode_bgra,decode_bgra

def build(out):
    out.mkdir(parents=True,exist_ok=False)
    w,h=408,132;raw=bytearray(w*h*4)
    def pixel(x,y,color):raw[(y*w+x)*4:(y*w+x+1)*4]=bytes((*color,255))
    for y in range(h):
        for x in range(w):
            c=(0,0,0)
            if x in (0,w-1) or y in (0,h-1):c=(255,255,255)
            elif y in (35,66,96):c=(96,96,96)
            elif x in (149,203,300):c=(64,64,64)
            if x<8 and y<8:c=(0,0,255)
            if x>=w-8 and y<8:c=(0,255,0)
            if x<8 and y>=h-8:c=(255,0,0)
            if x>=w-8 and y>=h-8:c=(0,255,255)
            pixel(x,y,c)
    raw=bytes(raw);rle=encode_bgra(raw)
    assert decode_bgra(rle,w*h)==raw and len(rle)<=0x14000
    def chunk(tag,b):return struct.pack('>I',len(b))+tag+b+struct.pack('>I',zlib.crc32(tag+b)&0xffffffff)
    rows=b''.join(b'\0'+b''.join(raw[(y*w+x)*4:(y*w+x)*4+3][::-1]+b'\xff' for x in range(w)) for y in range(h))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
    for name,data in [('marker.bgra',raw),('marker.rle32',rle),('marker.png',png)]: (out/name).write_bytes(data)
    result=dict(width=w,height=h,raw_bytes=len(raw),encoded_bytes=len(rle),raw_sha256=hashlib.sha256(raw).hexdigest(),encoded_sha256=hashlib.sha256(rle).hexdigest(),
        coordinates={'outer_border':[0,0,407,131],'horizontal_lines':[35,66,96],'vertical_lines':[149,203,300],'corner_square_size':8},
        network=False,live_drawing_allowed=False,resource_id=None,external_binding_established=False,
        color_note='Canonical BGRA. Do not assume road-icon red/blue correction applies to a future HUD surface binding.',
        reference_note='150x36 coordinate lines are source markers only, not registered physical V1 placement. Uniform scaling can preserve all markers without increasing physical height.')
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.output),indent=2))
