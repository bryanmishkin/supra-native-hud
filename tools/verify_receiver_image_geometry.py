#!/usr/bin/env python3
"""Offline execution of older receiver004 image decoder and fit branches.

Requires a private, hash-pinned receiver image. No vehicle/network operations.
The render backend and allocator are intercepted; this does not prove visibility.
"""
import argparse, hashlib, json, math, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import *
from ric_rle32 import encode_bgra, decode_bgra

SHA = '50130235f52573cc9facda89795486387ac4eb73a999026983694fd91d379761'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--image', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--request', type=Path, help='Optional private captured 36x36 B00E bitmap request')
a = p.parse_args()
raw = a.image.read_bytes()
if hashlib.sha256(raw).hexdigest() != SHA:
    raise SystemExit('Wrong receiver image: refusing version-specific offsets')

def cpu():
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x10000, (len(raw)+4095)&~4095)
    u.mem_write(0x10000, raw)
    u.mem_map(0x3000000, 0x200000)
    u.reg_write(UC_ARM_REG_SP, 0x31ff000)
    u.reg_write(UC_ARM_REG_LR, 0x31fe001)
    u.reg_write(UC_ARM_REG_C1_C0_2, 0xf00000)
    u.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return u

def ret(u):
    u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

cases=[]
for name, dims, target, expected in [
    ('unchanged-small', (36,36), (128,128), 1),
    ('height-limited', (277,160), (150,36), 36/160),
    ('width-limited', (300,36), (150,36), .5),
    ('both-limited', (300,160), (150,36), 36/160),
    ('larger-bound-rectangle', (277,160), (277,160), 1),
    ('portrait-bound-rectangle', (128,128), (28,70), 28/128),
]:
    u=cpu(); u.mem_write(0x3002000,struct.pack('<ff',*dims));u.mem_write(0x3003000,struct.pack('<ff',*target))
    u.reg_write(UC_ARM_REG_R1,0x3001000);u.reg_write(UC_ARM_REG_R2,0x3002000);u.reg_write(UC_ARM_REG_R3,0x3003000)
    scales=[]
    def hook(u,addr,size,data):
        if addr==0x256db2:
            u.mem_write(u.reg_read(UC_ARM_REG_R0),struct.pack('<II',u.reg_read(UC_ARM_REG_S0),u.reg_read(UC_ARM_REG_S1)));ret(u)
        elif addr==0x36b678:
            scales.append(struct.unpack('<ff',u.mem_read(u.reg_read(UC_ARM_REG_R1),8)));ret(u)
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x257061,0x31fe000,count=1000)
    assert u.reg_read(UC_ARM_REG_PC)==0x31fe000
    assert len(scales)==1 and all(math.isclose(s,expected,rel_tol=1e-6) for s in scales[0]),(name,scales)
    cases.append(dict(case=name,source=dims,bound_rectangle=target,scale=scales[0],rendered_extent=[dims[0]*scales[0][0],dims[1]*scales[0][1]]))

fixtures=[]
for n in [1,127,128,255]:
    pixels=bytes([0x12,0x34,0x56,255])*n+bytes([3,2,1,255])*3
    fixtures.append((f'repeat-boundary-{n}',encode_bgra(pixels),n+3,1))
for n in [127,128,255]:
    pixels=b''.join(bytes([i%256,i*3%256,i*7%256,255]) for i in range(n))
    fixtures.append((f'literal-boundary-{n}',encode_bgra(pixels),n,1))
if a.request:
    from ric_resource import decode_resource_body
    req=a.request.read_bytes()
    if req[:4]!=bytes.fromhex('b00e0003') or int.from_bytes(req[4:8],'big')!=len(req)-8 or req[12:16]!=bytes([1,1,0,0]):
        raise ValueError('Expected captured B00E method3 request')
    parsed=decode_resource_body(req[16:]);meta=parsed.get('bitmap',{})
    if meta.get('resolution_pair')!=[36,36] or not meta.get('outer_identity_matches') or meta.get('image_bytes',99999)>8192:
        raise ValueError('Expected bounded captured 36x36 fixture')
    fixtures.append(('captured-failed-ruler',req[46:],36,36))
decoders=[]
for name,data,w,h in fixtures:
    u=cpu();inp=0x3001000;out=0x3010000
    u.mem_write(inp,data);u.mem_write(out,b'\xa5'*(w*h*4+16))
    sp=u.reg_read(UC_ARM_REG_SP);u.mem_write(sp,struct.pack('<II',1,inp))
    u.reg_write(UC_ARM_REG_R0,w);u.reg_write(UC_ARM_REG_R1,h);u.reg_write(UC_ARM_REG_R2,len(data))
    allocations=[]
    def alloc(u,addr,size,unused):
        if addr==0x2d29e8:
            allocations.append(u.reg_read(UC_ARM_REG_R0));u.reg_write(UC_ARM_REG_R0,out);ret(u)
    u.hook_add(UC_HOOK_CODE,alloc);u.emu_start(0x2d303d,0x31fe000,count=200000)
    assert u.reg_read(UC_ARM_REG_PC)==0x31fe000
    got=bytes(u.mem_read(out,w*h*4));assert got==decode_bgra(data,w*h),name
    assert allocations==[w*h*4] and bytes(u.mem_read(out+w*h*4,16))==b'\xa5'*16
    decoders.append(dict(case=name,width=w,height=h,encoded_bytes=len(data),pixel_sha256=hashlib.sha256(got).hexdigest(),matches_bgra=True))
a.output.write_text(json.dumps(dict(image_sha256=SHA,scope='older004 firmware; synthetic geometry; no actual display output',fit_entry='0x257060',fit_intercepts=['vector constructor 0x256db2','render scale setter 0x36b678'],fit_cases=cases,decoder_entry='0x2d303c',decoder_intercepts=['allocator 0x2d29e8'],decoder_cases=decoders),indent=2)+'\n')
print(f'PASS: {len(cases)} geometry cases and {len(decoders)} receiver decoder cases')
