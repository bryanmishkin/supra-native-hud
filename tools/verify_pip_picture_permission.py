#!/usr/bin/env python3
"""Native tag19 capability decoding and PiP picture selection; offline only."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import *

def verify(path,payload):
    if len(payload)!=24 or payload[:2]!=bytes([19,7]):
        raise ValueError('Expected captured 24-byte high-intersection configuration')
    rows=[]
    for enabled in (0,1):
        for destination in (0,1):
            raw=bytearray(payload);raw[12]=enabled
            c=cpu_for(path,CTL);obj=BASE+0x1000;stream=BASE+0x2000;manager=BASE+0x3000;wrapper=BASE+0x4000;sender=BASE+0x5000;model=BASE+0x6000
            pos=[0];reads=[]
            def read(uc,a,size,user):
                if a!=0x12a04c:return
                st,dst,n=[uc.reg_read(x) for x in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
                assert st==stream and pos[0]+n<=len(raw)
                uc.mem_write(dst,bytes(raw[pos[0]:pos[0]+n]));reads.append(n);pos[0]+=n
                uc.reg_write(UC_ARM_REG_R0,n);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
            c.hook_add(UC_HOOK_CODE,read)
            c.reg_write(UC_ARM_REG_R0,stream);c.reg_write(UC_ARM_REG_R1,obj);c.reg_write(UC_ARM_REG_LR,BASE)
            c.emu_start(0xbc8c78,BASE,count=10000)
            assert c.reg_read(UC_ARM_REG_PC)==BASE and pos[0]==24
            c.reg_write(UC_ARM_REG_R0,manager);c.reg_write(UC_ARM_REG_R1,obj);c.reg_write(UC_ARM_REG_LR,BASE)
            c.emu_start(0xa24ca4,BASE,count=1000)
            assert c.reg_read(UC_ARM_REG_PC)==BASE
            assert c.mem_read(manager+0x1b2,1)[0]==enabled
            word(c,wrapper+4,manager);word(c,sender+0x14,wrapper);word(c,sender+0x20,destination)
            word(c,model+0x34,0x02000003);word(c,model+0x38,0x02000004)
            c.reg_write(UC_ARM_REG_R0,wrapper);c.reg_write(UC_ARM_REG_R4,model);c.reg_write(UC_ARM_REG_R5,sender)
            c.reg_write(UC_ARM_REG_SP,BASE+0xe000)
            c.emu_start(0xab47cc,0xab4804,count=100)
            assert c.reg_read(UC_ARM_REG_PC)==0xab4804
            image=struct.unpack('<I',c.mem_read(BASE+0xe000+0xe8,4))[0]
            expected=(0x02000003 if destination else 0x02000004) if enabled else 0xffffffff
            assert image==expected
            rows.append({'picture_supported':enabled,'destination_selector':destination,'selected_picture_id':hex(image),'stream_read_sizes':reads})
    return {'sha256':CTL,'captured_payload_sha256':__import__('hashlib').sha256(payload).hexdigest(),'captured_picture_supported':payload[12], 'cases':rows,'executed':['native config decoder0xbc8c78','native config setter0xa24ca4','native picture gate0xab47cc'],'callbacks':'bounded input stream reads only','limitation':'Controlled gate inputs; does not establish active runtime values or windshield rendering.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('controller',type=Path);p.add_argument('config_payload',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.controller,a.config_payload.read_bytes()),indent=2))
