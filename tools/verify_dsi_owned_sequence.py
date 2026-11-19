#!/usr/bin/env python3
"""Execute captured Colibry constructor sequence selection, offline only."""
import argparse, json, struct
from pathlib import Path
from verify_pip_binding_records import *
SHA='adec5e17c4f4f4826de2eeee2aa2f3c5bf27de7e8edc3e107b79fa2ca6a88c10'

def verify(path):
    cases=[]
    for supplied in (0,37,0x12345678):
        c=cpu_for(path,SHA)
        owner,channel,tcp,client,server=[BASE+i for i in (0x1000,0x2000,0x3000,0x4000,0x5000)]
        stack=BASE+0xf000;called=[]
        c.mem_write(channel,struct.pack('<II',9,10));c.mem_write(client,struct.pack('<II',11,12));c.mem_write(server,struct.pack('<II',13,14))
        for i,value in enumerate((0x100,7,3,client,server,supplied)):word(c,stack+4*i,value)
        stubs={0x24d08:'stream base constructor',0x25290:'console constructor',0x25998:'service registry lookup (absent)',0x25368:'temporary string destructor',0x26994:'ID allocator (fixed test value 91)'}
        def boundary(cpu,address,size,user):
            if address in stubs:
                called.append(stubs[address]);cpu.reg_write(UC_ARM_REG_R0,91 if address==0x26994 else 0)
                cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        c.hook_add(UC_HOOK_CODE,boundary)
        for reg,value in ((UC_ARM_REG_R0,owner),(UC_ARM_REG_R1,channel),(UC_ARM_REG_R2,tcp),(UC_ARM_REG_R3,0xffffffff),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,BASE)):
            c.reg_write(reg,value)
        c.emu_start(0x3c104,BASE,count=500)
        actual=struct.unpack('<III',bytes(c.mem_read(owner+0x44,12)))
        assert actual==(0x100,3,supplied or 91)
        assert ('ID allocator (fixed test value 91)' in called)==(supplied==0)
        cases.append({'supplied_sequence':supplied,'stream_request_type_id_sequence':list(actual),'intercepts':called})
    return {'sha256':SHA,'constructor':'0x3c104','cases':cases,'result':'Nonzero last constructor argument is retained verbatim as request sequence. Zero invokes allocator.','limitation':'Native sequence selection only; ancillary constructors, registry, string destruction and ID allocator are intercepted. No broker or vehicle contact.'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('colibry',type=Path)
    print(json.dumps(verify(p.parse_args().colibry),indent=2))
