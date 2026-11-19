#!/usr/bin/env python3
"""Compare captured native MOCCA/Colibry unfragmented send boundaries offline.
Synthetic equal routing fields are deliberate inputs, not discovered live party IDs.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from verify_pip_binding_records import *

MOCCA = '140ee2e9816b91b58f6b0d81df6a609e533035892710c54c4e520147a548ff15'
COLIBRY = 'adec5e17c4f4f4826de2eeee2aa2f3c5bf27de7e8edc3e107b79fa2ca6a88c10'


def frame(path, sha, mocca, payload, request, sequence, request_type=0x100):
    c=cpu_for(path,sha)
    owner,buffer,descriptor,socket=BASE+0x1000,BASE+0x2000,BASE+0x3000,BASE+0x4000
    header=struct.pack('<IHHIIIIIIII',0x200,4,0,1,2,3,4,7,1,0,0)
    prefix=struct.pack('<IIII',0,request_type,request,sequence)
    captured=[]
    if mocca:
        c.mem_write(buffer+40,prefix+payload)
        for offset,value in [(0x18,1024-len(prefix+payload)),(0x48,buffer+40+len(prefix+payload)),
                             (0x50,40+len(prefix+payload)),(0x14,1064),(0x10,buffer),(0xa4,descriptor),(0xb0,socket)]:
            word(c,owner+offset,value)
        c.mem_write(owner+0xac,b'\x01\x01')
        c.mem_write(owner+0x20,header)
    else:
        c.mem_write(owner+0x18,header)
        c.mem_write(owner+0x40,prefix)
        c.mem_write(buffer,payload or b'\x00')
        word(c,owner+8,len(payload));word(c,owner+0x10,buffer);word(c,owner+0x60,socket)
    def boundary(cpu,address,size,user):
        if mocca and address==0x5e97c:
            destination,source,count=[cpu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            assert count==40
            cpu.mem_write(destination,bytes(cpu.mem_read(source,count)))
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        if mocca and address==0x63548:
            source,count=cpu.reg_read(UC_ARM_REG_R1),cpu.reg_read(UC_ARM_REG_R2)
            captured.append(bytes(cpu.mem_read(source,count)))
            cpu.reg_write(UC_ARM_REG_R0,count);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        if not mocca and address==0x26b20:
            vector,count=cpu.reg_read(UC_ARM_REG_R1),cpu.reg_read(UC_ARM_REG_R2)
            assert count==3
            data=b''
            for i in range(count):
                pointer,length=struct.unpack('<II',bytes(cpu.mem_read(vector+8*i,8)))
                if length:data+=bytes(cpu.mem_read(pointer,length))
            captured.append(data)
            cpu.reg_write(UC_ARM_REG_R0,len(data));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
    c.hook_add(UC_HOOK_CODE,boundary)
    c.reg_write(UC_ARM_REG_R0,owner);c.reg_write(UC_ARM_REG_LR,BASE)
    c.emu_start(0x9d580 if mocca else 0x3b828,BASE,count=1000)
    assert c.reg_read(UC_ARM_REG_PC)==BASE and len(captured)==1
    expected=bytearray(header)
    struct.pack_into('<I',expected,28,0)
    struct.pack_into('<I',expected,32,16+len(payload))
    assert captured[0]==bytes(expected)+prefix+payload
    return captured[0]


def verify(mocca,colibry):
    colibry_sha=COLIBRY
    rows=[]
    for request,payload,kind in [(3,struct.pack('<II',0,0x0300206d),0x100),(3,struct.pack('<II',0xfffffffe,0x030020d2),0x100),(7,b'',0x100),(0x80000004,b'',0x105),(0x80000004,b'',0x106),(6,b'',0x100)]:
        a=frame(mocca,MOCCA,True,payload,request,37,kind)
        b=frame(colibry,colibry_sha,False,payload,request,37,kind)
        assert a==b
        rows.append({'event_id':request,'request_type':kind,'frame_hex':a.hex(),'identical':True})
    return {'mocca_sha256':MOCCA,'colibry_sha256':colibry_sha,'cases':rows,
      'limitation':'Actual native unfragmented send/flush with equal synthetic route IDs and request prefix. memcpy and socket send boundaries intercepted. Does not establish live service registration, response semantics, identity ownership, attachment or windshield rendering.',
      'vehicle_contact':False,'receiver_acceptance_proven':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mocca',type=Path,required=True);p.add_argument('--colibry',type=Path,required=True)
    a=p.parse_args();print(json.dumps(verify(a.mocca,a.colibry),indent=2))
