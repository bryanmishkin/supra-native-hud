#!/usr/bin/env python3
"""Offline A32 call-chain audit of actual Supra PiP vs bitmap B006 serializers.

No vehicle/network code. Requires byte-identical archived controller binary.
"""
import argparse,hashlib,json,struct
from pathlib import Path

SHA='71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a'
END={0xbb51e8:0xbb5284,0xbb5158:0xbb51dc,0xbb50c0:0xbb514c,
     0xbb501c:0xbb50b8,0xbb4f84:0xbb5010,0xbb6350:0xbb63dc}
PIP={0xbb51e8:[0xbb5158],0xbb5158:[0xbb50c0,0xba95b0],
     0xbb50c0:[0xbb501c,0xba9528],0xbb501c:[0xbb4f84],
     0xbb4f84:[0xba8248,0xbb4334]}
BITMAP={0xbb6350:[0xbb4ee0,0xbb58d4]}

def offset(raw,address):
    if raw[:6]!=b'\x7fELF\x01\x01' or struct.unpack_from('<H',raw,18)[0]!=40:
        raise ValueError('Expected ARM ELF32 little-endian')
    table=struct.unpack_from('<I',raw,28)[0]
    width,count=struct.unpack_from('<H',raw,42)[0],struct.unpack_from('<H',raw,44)[0]
    for i in range(count):
        typ,paddr,vaddr,_,length,_,_,_=struct.unpack_from('<IIIIIIII',raw,table+i*width)
        if typ==1 and vaddr<=address<vaddr+length:
            at=paddr+address-vaddr
            if at+4<=len(raw):return at
    raise ValueError('Unmapped address '+hex(address))

def calls(raw,start,end):
    found=set()
    for addr in range(start,end,4):
        word=struct.unpack_from('<I',raw,offset(raw,addr))[0]
        if word&0x0f000000!=0x0b000000:continue
        delta=(word&0xffffff)<<2
        if delta&(1<<25):delta-=1<<26
        found.add((addr+8+delta)&0xffffffff)
    return found

def audit(path):
    raw=path.read_bytes()
    h=hashlib.sha256(raw).hexdigest()
    if h!=SHA:raise ValueError('Target firmware hash mismatch '+h)
    results=[];pip_targets=set()
    for group,graph in [('PiP variant 3',PIP),('Bitmap variant 2',BITMAP)]:
        for caller,edges in graph.items():
            actual=calls(raw,caller,END[caller])
            verified=all(edge in actual for edge in edges)
            results.append({'group':group,'caller':hex(caller),
                            'required_calls':[hex(x) for x in edges],
                            'verified':verified})
            if group=='PiP variant 3':pip_targets.update(actual)
    if not all(x['verified'] for x in results):
        raise ValueError('Serializer call-chain mismatch')
    if 0xbb58d4 in pip_targets:raise ValueError('PiP path unexpectedly calls bitmap pixel-array serializer')
    return {'schema':1,'controller_sha256':h,'vehicle_io':False,'commands_sent':0,
            'bitmap_variant2_calls_pixel_writer_0xbb58d4':True,
            'pip_variant3_calls_pixel_writer_in_traced_chain':False,
            'checks':results,
            'conclusion':'Do not send V1 bitmap bytes as PiP type2/variant3. The traced PiP chain writes fixed descriptor fields, not the bitmap pixel-byte array.',
            'limits':'Other PiP producers, attachments and windshield display routes remain unverified.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('controller',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    result=audit(a.controller)
    text=json.dumps(result,indent=2)+'\n'
    if a.output:a.output.write_text(text)
    print(text,end='')
