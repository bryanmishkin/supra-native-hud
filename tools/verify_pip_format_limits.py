#!/usr/bin/env python3
"""Execute retained factory PiP format-limit checks offline; no vehicle access.

The intercepted logger records the out-of-range branch; it is not a receiver
ACK or evidence that any particular native video format reaches the windshield.
"""
import argparse
import hashlib
import json
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

EXPECTED='71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a'

def verify(path):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=EXPECTED:
        raise ValueError('Wrong factory binary; fixed-address execution refused')
    cpu=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    with path.open('rb') as f:
        segments=[s for s in ELFFile(f).iter_segments() if s['p_type']=='PT_LOAD']
        low=min(s['p_vaddr'] for s in segments)&~4095
        high=max(s['p_vaddr']+s['p_memsz'] for s in segments)
        cpu.mem_map(low,((high+4095)&~4095)-low)
        for s in segments:cpu.mem_write(s['p_vaddr'],data[s['p_offset']:s['p_offset']+s['p_filesz']])
    base=0x20000000;cpu.mem_map(base,8192);stop=base+0x1f00
    logs=[]
    def hook(uc,address,size,user):
        if address==0x1286a8:
            logs.append(address);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        elif not (0xaadd48<=address<0xaadde0 or address==stop):
            raise ValueError('Unexpected call outside bounded check: '+hex(address))
    cpu.hook_add(UC_HOOK_CODE,hook)
    cases=[]
    for name,start,offset,maxima in [('depth',0xaadd94,0x9c,range(2)),('packing',0xaadd48,0x9d,range(3))]:
        for maximum in maxima:
            for selected in range(3):
                logs.clear();cpu.mem_write(base,bytes(1024))
                cpu.mem_write(base+4,(base+256).to_bytes(4,'little'))
                cpu.mem_write(base+256+offset,bytes([maximum]))
                cpu.reg_write(UC_ARM_REG_R0,base);cpu.reg_write(UC_ARM_REG_R1,selected)
                cpu.reg_write(UC_ARM_REG_SP,base+0x1800);cpu.reg_write(UC_ARM_REG_LR,stop)
                cpu.emu_start(start,stop,count=100)
                if cpu.reg_read(UC_ARM_REG_PC)!=stop or bool(logs)!=(selected>maximum):
                    raise AssertionError('Factory limit semantics differ')
                cases.append(dict(field=name,maximum=maximum,selected=selected,out_of_range_log=bool(logs)))
    return dict(binary_sha256=EXPECTED,cases=cases,matching_cases=len(cases),
                conclusion='Selected value <= advertised maximum avoids factory out-of-range diagnostic',
                receiver_execution=False,windshield_delivery_proven=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('controller',type=Path)
    print(json.dumps(verify(p.parse_args().controller),indent=2))
