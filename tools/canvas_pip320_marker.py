#!/usr/bin/env python3
"""Generate an asymmetric opaque 320x320 PIP clipping/alignment test card.

Host-only; DOES NOT encode PIP variant-3 or communicate with the car. PNG is
for operator preview; BGRA pixels must be encoded with the verified target
serializer before any proposed live trial. No presumed windshield XY coords.
"""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
SIZE=320
COLORS=((255,0,0),(0,255,0),(0,0,255),(255,255,0)) # RGB corner coding

def marker():
    w=h=SIZE
    data=bytearray(w*h*4)
    def rect(x0,y0,x1,y1,rgb):
        b,g,r=rgb[2],rgb[1],rgb[0]
        for y in range(max(0,y0),min(h,y1)):
            for x in range(max(0,x0),min(w,x1)):
                i=4*(y*w+x);data[i:i+4]=bytes((b,g,r,255))
    rect(0,0,w,h,(4,7,12))
    # A 5-pixel inset white frame immediately reveals clipping.
    rect(5,5,w-5,9,(255,255,255));rect(5,h-9,w-5,h-5,(255,255,255))
    rect(5,5,9,h-5,(255,255,255));rect(w-9,5,w-5,h-5,(255,255,255))
    for i,color in enumerate(COLORS):
        x=15 if i%2==0 else w-53
        y=15 if i<2 else h-53
        rect(x,y,x+38,y+38,color)
    rect(w//2-2,30,w//2+2,h-30,(230,230,230))
    rect(30,h//2-2,w-30,h//2+2,(230,230,230))
    # Scale increments on the edges (21px ticks every 40px).
    for x in range(40,w-39,40):rect(x-1,5,x+1,26,(180,180,180))
    for y in range(40,h-39,40):rect(5,y-1,26,y+1,(180,180,180))
    return bytes(data)

def png(raw):
    if len(raw)!=SIZE*SIZE*4:raise ValueError('Wrong pixel count')
    def chunk(tag,body):return struct.pack('>I',len(body))+tag+body+struct.pack('>I',zlib.crc32(tag+body)&0xffffffff)
    scan=bytearray()
    for y in range(SIZE):
        scan.append(0)
        for x in range(SIZE):
            off=4*(y*SIZE+x);b,g,r,a=raw[off:off+4];scan.extend((r,g,b,a))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',SIZE,SIZE,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(bytes(scan),9))+chunk(b'IEND',b'')

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path)
    a=p.parse_args(argv)
    if not a.output:
        print('Host-only PIP 320 test-card generator; pass --output to a NEW directory. No vehicle I/O.');return 0
    if a.output.exists():p.error('Refusing to overwrite existing output directory')
    a.output.mkdir(parents=True)
    bgra=marker();preview=png(bgra)
    (a.output/'pip320-marker.bgra').write_bytes(bgra)
    (a.output/'pip320-preview.png').write_bytes(preview)
    record={'size':[320,320],'raw_format':'opaque BGRA',
            'bgra_sha256':hashlib.sha256(bgra).hexdigest(),
            'png_sha256':hashlib.sha256(preview).hexdigest(),
            'variant_3_encoded':False,'vehicle_draw_approved':False,
            'use':'Future reviewed PiP variant-3 static placement / clipping trial; do not inject raw BGRA'}
    (a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

