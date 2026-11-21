#!/usr/bin/env python3
"""Offline named-bitmap lookup/removal in receiver004. No external binding claim."""
import argparse, hashlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from verify_hud_uploaded_image_path import SHA

def verify(path):
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==SHA
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    u.mem_map(0x10000,(len(raw)+4095)&~4095);u.mem_write(0x10000,raw)
    u.mem_map(0x2900000,0x100000);u.mem_map(0x3000000,0x100000)
    provider,node,name,bitmap,stop=0x29be320,0x3002000,0x3003000,0x3004000,0x30ff000
    # DefaultAssetProvider constructor stores this exact vtable at object+0x1c.
    vt=0xaacc04
    getter=struct.unpack('<I',u.mem_read(vt+0x6c,4))[0]
    release=struct.unpack('<I',u.mem_read(vt+0x74,4))[0]
    assert (getter,release)==(0x2e85b4,0x2e85bc)
    key=b'Imports#hud#hud_TestBmp#offline_probe'
    u.mem_write(name,key+b'\0');u.mem_write(bitmap,b'\xa5'*64)
    u.mem_write(provider+0x1c,struct.pack('<I',vt))
    # Native tree layout: encoded size/flags=one node, root; key length/name/value.
    u.mem_write(provider+0x80,struct.pack('<II',2,node))
    u.mem_write(node,struct.pack('<8I',len(key),name,bitmap,0,0,0,0,0))
    u.mem_write(0x29be744,struct.pack('<I',1))
    u.mem_write(0x29be31c,b'\1');u.mem_write(0x29be718,struct.pack('<I',1))
    intercepted=[]
    def hook(uc,addr,size,data):
        if addr in (0x383584,0x3835c0,0x13866c):
            intercepted.append({'address':hex(addr),'r0':hex(uc.reg_read(UC_ARM_REG_R0))})
            uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE,hook)
    def call(entry,third=0):
        for reg,value in ((UC_ARM_REG_SP,0x30fe000),(UC_ARM_REG_LR,stop),(UC_ARM_REG_R0,provider),(UC_ARM_REG_R1,name),(UC_ARM_REG_R2,third)):u.reg_write(reg,value)
        u.emu_start(entry,stop,count=100000)
        assert u.reg_read(UC_ARM_REG_PC)==stop
        return u.reg_read(UC_ARM_REG_R0)
    assert call(getter)==bitmap
    assert struct.unpack('<I',u.mem_read(provider+0x84,4))[0]==node
    # Exact caller convention: release(name,0) removes entry without bitmap destroy.
    assert call(release)==bitmap
    assert struct.unpack('<I',u.mem_read(provider+0x84,4))[0]==0
    assert bytes(u.mem_read(bitmap,64))==b'\xa5'*64
    assert [x['r0'] for x in intercepted if x['address']=='0x13866c']==[hex(node)]
    return dict(passed=True,image_sha256=SHA,vtable=hex(vt),getter=hex(getter),release=hex(release),native_name_lookup=True,native_tree_removal=True,bitmap_bytes_unchanged=True,intercepted=intercepted,
      scope='DefaultAssetProvider candidate selected by vtable and constructor evidence; synthetic one-node cache with opaque bitmap. Not a runtime observation of the widget manager. Singleton initialization flags are preset; its getter executes natively. Only mutex operations and node deallocation intercepted. No cache-miss loading, bitmap allocation, GPU, Ethernet or vehicle execution; no external insertion route established.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=verify(a.image);a.output.write_text(json.dumps(r,indent=2)+'\n');print('PASS: native named bitmap cache hit and removal; bitmap retained; offline only')
