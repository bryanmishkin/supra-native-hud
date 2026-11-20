#!/usr/bin/env python3
"""Execute older receiver firmware offline: initialized registration, raw request
parser, validation, dispatch, application control and completion. Never connects.
Requires Unicorn and the owner's private 004 auxiliary firmware image.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1

STOP=0x300fff0
IMAGE_SHA='b82697e4767f26a006554d6c41ec2dbc06be074489ee7a33dca79097ac7023b6'

def verify(image):
    b=image.read_bytes()
    assert hashlib.sha256(b).hexdigest()==IMAGE_SHA, 'Firmware hash mismatch'
    cases=[]
    for sub,args,state in [(1,[0,16,32,48],7),(1,[92,0,0,0],7),(2,[],7),(1,[0,16,32,48],6),(2,[],6),(1,[0,16,32],7),(3,[],7)]:
        u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
        for a,n in [(0,0x40000),(0x1000000,0x180000),(0x1a00000,0x100000),(0x3000000,0x10000),(0xb0600000,0x100000)]:u.mem_map(a,n)
        u.mem_write(0x1000000,b);u.reg_write(UC_ARM_REG_SP,0x300f000);u.reg_write(UC_ARM_REG_R0,0x1000184)
        u.emu_start(0x100045d,0x1000942,count=10000000)
        assert u.reg_read(UC_ARM_REG_PC)==0x1000942
        registration=bytes(u.mem_read(0x1d5a8+88*16,16))
        assert registration.hex()=='310002a1000000000100000000000000'
        stubs=[];responses=[]
        def hook(uc,a,size,data):
            if a in (0x104540c,0x1045468,0x1046b9c):
                stubs.append(hex(a));uc.reg_write(UC_ARM_REG_R0,0);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
            if a==0x102cade:
                p=uc.reg_read(UC_ARM_REG_R0);n=uc.reg_read(UC_ARM_REG_R1)
                responses.append(bytes(uc.mem_read(p,n)).hex())
        u.hook_add(UC_HOOK_CODE,hook)
        def call(pc,r0,r1=0):
            u.reg_write(UC_ARM_REG_SP,0x300f000);u.reg_write(UC_ARM_REG_LR,STOP|1)
            u.reg_write(UC_ARM_REG_R0,r0);u.reg_write(UC_ARM_REG_R1,r1)
            u.emu_start(pc|1,STOP,count=1000000)
            assert u.reg_read(UC_ARM_REG_PC)==STOP, hex(u.reg_read(UC_ARM_REG_PC))
            return u.reg_read(UC_ARM_REG_R0)
        raw=bytes([sub,0xa1,2]+args)
        source,rawptr,out,descriptor=0x3001000,0x3002000,0x3003000,0x3004000
        u.mem_write(rawptr,raw)
        u.mem_write(source,struct.pack('<IH',rawptr,len(raw)))
        u.mem_write(source+8,struct.pack('<I',out));u.mem_write(source+0x14,struct.pack('<H',256));u.mem_write(source+0x1a,bytes([sub]))
        assert call(0x10f84be,source,descriptor)==1
        # Synthetic diagnostic context and operating state; no session change command.
        u.mem_write(0x198b8,struct.pack('<I',0x3006000));u.mem_write(0x18e42,b'\1')
        u.mem_write(0x3fb8,bytes([state]));u.mem_write(0x4a28,bytes([92,8,9,10,1]))
        u.mem_write(descriptor+8,struct.pack('<I',2))
        assert call(0x10f3fd0,descriptor)==0, 'Registration validation failed'
        u.mem_write(descriptor+8,struct.pack('<I',3))
        assert call(0x10f3fd0,descriptor)==10, 'Expected asynchronous dispatch'
        copied=bytes(u.mem_read(0x53d4,0x6a))
        assert copied[:3]==bytes([2,0xa1,sub]) and copied[3:3+len(raw)]==raw
        assert struct.unpack_from('<H',copied,0x68)[0]==len(raw)
        call(0x10ec968,0)
        result=call(0x10f3fd0,descriptor)
        final=list(u.mem_read(0x4a28,5));nrc=u.mem_read(descriptor+0xc,1)[0]
        expected_nrc=0x22 if state<7 else 0x13 if sub==1 and len(args)!=4 else 0x31 if sub==3 else 0
        assert nrc==expected_nrc and result==int(bool(expected_nrc))
        expected=(args+[1] if sub==1 else [0,0,0,0,2]) if not expected_nrc else [92,8,9,10,1]
        assert final==expected
        cases.append(dict(request=(b'\x31'+raw).hex(),operating_state=state,registration=registration.hex(),control=final,nrc=nrc,internal_responses=responses,os_stub_calls=stubs))
    return dict(image_sha256=IMAGE_SHA,cases=cases,passed=True,
        limitations='004 firmware, not installed 008. Native initialization and parser/registration/dispatch/control/completion executed. OS critical sections and event notification stubbed; async scheduling advanced manually. Synthetic session=1 and operating-state=7 or6. HSFZ transport, renderer and physical display not executed. Stop also requires operating-state>=7. No ECU-side expiry proven.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=verify(a.image);a.output.write_text(json.dumps(result,indent=2)+'\n');print('Seven native request/cleanup/negative cases passed:',a.output)
