#!/usr/bin/env python3
"""Execute captured HU guidance selector, substituting vector storage operations only."""
import argparse,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from verify_pip_binding_records import cpu_for,word,CTL,BASE


def verify(path):
    results=[]
    for hud,kombi,pair in [(False,0,(4301,4402)),(False,1,(5301,5402)),(True,0,(8301,8402)),(True,1,(8301,8402))]:
        for preferred in (0,1):
            for ids in [[],[pair[0]],[pair[1]],list(pair),[pair[0]+1]]:
                c=cpu_for(path,CTL);obj=BASE+0x1000;manager=BASE+0x1100;items=BASE+0x2000;data=BASE+0x2100;output=BASE+0x3000;selected=BASE+0x3100
                word(c,obj+4,manager);c.mem_write(obj+8,bytes([preferred]));word(c,manager+0x14,kombi);c.mem_write(manager+0x18,bytes([hud]))
                word(c,items+4,data if ids else 0);word(c,items+8,data+len(ids)*4 if ids else 0)
                for i,v in enumerate(ids):word(c,data+i*4,v)
                appended=[]
                def boundary(cpu,a,size,user):
                    if a==0x12b5d0:
                        assert cpu.reg_read(UC_ARM_REG_R0)==output;appended.clear()
                    elif a==0x2b0880:
                        assert cpu.reg_read(UC_ARM_REG_R0)==items
                        i=cpu.reg_read(UC_ARM_REG_R1);assert i<len(ids);cpu.reg_write(UC_ARM_REG_R0,data+4*i)
                    elif a==0x2bd744:
                        assert cpu.reg_read(UC_ARM_REG_R0)==output
                        appended.append(struct.unpack('<I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),4)))[0])
                    else:return
                    cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
                c.hook_add(UC_HOOK_CODE,boundary)
                for reg,value in [(UC_ARM_REG_R0,obj),(UC_ARM_REG_R1,items),(UC_ARM_REG_R2,output),(UC_ARM_REG_R3,selected),(UC_ARM_REG_LR,BASE)]:c.reg_write(reg,value)
                c.emu_start(0xa8699c,BASE,count=3000);assert c.reg_read(UC_ARM_REG_PC)==BASE
                chosen=struct.unpack('<I',bytes(c.mem_read(selected,4)))[0]
                expected=(pair[0] if pair[0] in ids else pair[1] if pair[1] in ids else 0) if preferred else (pair[1] if pair[1] in ids else 0)
                assert chosen==expected,(hud,kombi,preferred,ids,chosen,expected)
                assert bool(c.reg_read(UC_ARM_REG_R0))==bool(chosen)
                results.append(dict(hud=hud,kombi=kombi,preference_byte=preferred,available=ids,chosen=chosen,appended=appended))
    return dict(controller_sha256=CTL,cases=results,matching_cases=len(results),vehicle_contact=False,receiver_delivery_proven=False,
                limitation='Real HU selector/helper instructions; vector clear/append/index boundaries substituted. Available type lists are test inputs, not observed live maneuver lists.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('controller',type=Path)
    print(json.dumps(verify(p.parse_args().controller),indent=2))
