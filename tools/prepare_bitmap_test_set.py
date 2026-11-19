#!/usr/bin/env python3
"""Build offline marker fixtures. Never connects to or selects vehicle resources."""
import argparse, hashlib, json, struct, zlib
from pathlib import Path
from ric_rle32 import encode_bgra, decode_bgra, marker_bgra

def trident(w,h):
    # Original geometric IU-style test glyph, not an official university asset.
    rects=[(.40,.05,.60,.15),(.46,.15,.54,.90),(.34,.89,.66,.98),
           (.10,.19,.30,.29),(.18,.29,.26,.67),(.18,.60,.82,.70),
           (.74,.29,.82,.67),(.70,.19,.90,.29)]
    raw=bytearray(w*h*4)
    side=min(w-8,h-8); ox=(w-side)/2; oy=(h-side)/2
    for y in range(h):
        for x in range(w):
            u=(x-ox)/side;v=(y-oy)/side
            lit=any(a<=u<b and c<=v<d for a,c,b,d in rects)
            border=x in (1,w-2) or y in (1,h-2)
            raw[(y*w+x)*4:(y*w+x+1)*4]=bytes((255,255,255,255) if lit else ((80,80,80,255) if border else (0,0,0,255)))
    return bytes(raw)

def png(raw,w,h):
    def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
    rows=b''.join(b'\0'+b''.join(bytes((raw[i+2],raw[i+1],raw[i],raw[i+3])) for i in range(y*w*4,(y+1)*w*4,4)) for y in range(h))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')

def build(out):
    out.mkdir(parents=True,exist_ok=False); cases=[]
    for w,h,path in [(150,36,'B006-road-icon'),(36,36,'B00E-bitmap-candidate'),(128,128,'B00E-bitmap-candidate')]:
        for shape in ['cross','iu-trident']:
            name=f'{path}-{w}x{h}-{shape}';raw=marker_bgra(w,h) if shape=='cross' else trident(w,h)
            encoded=encode_bgra(raw)
            if decode_bgra(encoded,w*h)!=raw:raise ValueError('RLE round-trip mismatch')
            files={}
            for ext,data in [('bgra',raw),('rle32',encoded),('png',png(raw,w,h))]:
                p=out/(name+'.'+ext);p.write_bytes(data);files[p.name]=hashlib.sha256(data).hexdigest()
            cases.append(dict(name=name,dimensions=[w,h],visible_seconds=30,files=files,
                path=path,asset_ready=True,vehicle_authorization=False,
                binding_status='previously verified path; new marker untested' if path.startswith('B006') else 'unproven model image reference and resource ownership',
                live_ready=False))
    result=dict(schema=1,notes=['No session handles, resource IDs, packets or network sender included.',
        'IU glyph is an original geometric test approximation.',
        'Dimensions are bitmap dimensions, not proven windshield canvas dimensions.',
        '36x36 B00E fixture is a size candidate, not proof smaller images are accepted.',
        'B006 runner requires a 150x36 opaque BGRA image; do not feed B00E candidates to it.'],cases=cases)
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);a=p.parse_args();print(json.dumps(build(a.output),indent=2))
