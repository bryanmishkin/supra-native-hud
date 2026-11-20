#!/usr/bin/env python3
"""Execute the captured controller's map-window size clamp; no vehicle I/O."""
import argparse
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_LR, UC_ARM_REG_PC
from verify_pip_binding_records import cpu_for, CTL, BASE, word


def verify(controller):
    results=[]
    cases=[((0,0,800,480),(800,480)),
           ((11,17,1600,600),(1440,540)),
           ((11,17,320,200),(1440,540)),
           ((11,17,1441,540),(1440,540)),
           ((11,17,1440,541),(1440,540))]
    for rectangle,limit in cases:
        cpu=cpu_for(controller,CTL)
        owner,rect=BASE+0x1000,BASE+0x4000
        word(cpu,owner+0x174,limit[0]);word(cpu,owner+0x178,limit[1])
        label=BASE+0x5000
        word(cpu,owner+0x1724,label)
        cpu.mem_write(label,bytes(64))
        cpu.mem_write(rect-4,b'GUAR'+struct.pack('<4I',*rectangle)+b'DEND')
        cpu.reg_write(UC_ARM_REG_R0,owner);cpu.reg_write(UC_ARM_REG_R1,rect)
        cpu.reg_write(UC_ARM_REG_LR,BASE)
        logs=[]
        def trace(uc,address,size,user):
            if address==0x1286a8:
                logs.append(address)
                uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
            elif not 0x754420<=address<=0x7544a4:
                raise RuntimeError('Unexpected external execution: '+hex(address))
        cpu.hook_add(UC_HOOK_CODE,trace)
        cpu.emu_start(0x754420,BASE,count=150)
        assert cpu.reg_read(UC_ARM_REG_PC)==BASE
        actual=struct.unpack('<4I',bytes(cpu.mem_read(rect,16)))
        expected=rectangle[:2]+tuple(min(a,b)for a,b in zip(rectangle[2:],limit))
        assert actual==expected
        assert bytes(cpu.mem_read(rect-4,4))==b'GUAR'
        assert bytes(cpu.mem_read(rect+16,4))==b'DEND'
        results.append(dict(input=rectangle,stored_limit=limit,output=actual,logging_calls_skipped=len(logs)))
    return dict(controller_sha256=CTL,cases=results,vehicle_contact=False,
                proves='Native map-window clamp preserves origin and caps width/height to owner+174/+178.',
                does_not_prove='These synthetic inputs are not actual vehicle dimensions. No windshield parent, receiver clip, live window, or new drawable area is simulated.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('controller',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.controller),indent=2))
