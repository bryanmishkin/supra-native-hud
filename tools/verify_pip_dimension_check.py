#!/usr/bin/env python3
"""Execute captured HU PiP dimension check; does not emulate the receiver."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import cpu_for,word,BASE,CTL
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC

def verify(path):
    cpu=cpu_for(path,CTL);owner=BASE+0x100;config=BASE+0x1000;vector=BASE+0x2000;data=BASE+0x2100;limits=BASE+0x2200;stack=BASE+0xf000
    logs=[];calls=[]
    def hook(uc,a,size,user):
        if a==0x1286a8:
            sp=uc.reg_read(UC_ARM_REG_SP)
            logs.append(list(struct.unpack('<5I',bytes(uc.mem_read(sp,20)))))
            uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        elif a==0xaae03c:calls.append(a)
        elif not (0xaae03c<=a<0xaae19c or 0xaae1a8<=a<0xaae1ec or a==BASE):
            raise RuntimeError('unexpected branch '+hex(a))
    cpu.hook_add(UC_HOOK_CODE,hook)
    cases=[]
    for w,h in [(150,36),(320,200),(320,320),(460,237),(800,480),(321,1),(1,321),(0,0)]:
        cpu.mem_write(BASE+0x100,bytes(0x3000));logs.clear();calls.clear()
        word(cpu,owner+4,config)
        for v,ptr in [(vector,data),(config+0x8c,limits)]:
            word(cpu,v+4,ptr);word(cpu,v+8,ptr+4);word(cpu,v+12,ptr+4)
        cpu.mem_write(data,struct.pack('<HH',w,h));cpu.mem_write(limits,struct.pack('<HH',320,320))
        before=bytes(cpu.mem_read(BASE+0x100,0x3000))
        for reg,value in [(UC_ARM_REG_R0,owner),(UC_ARM_REG_R1,0x02000004),(UC_ARM_REG_R2,2),(UC_ARM_REG_R3,vector),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,BASE)]:cpu.reg_write(reg,value)
        cpu.emu_start(0xaae1a8,BASE,count=1000)
        assert cpu.reg_read(UC_ARM_REG_PC)==BASE
        assert bytes(cpu.mem_read(BASE+0x100,0x3000))==before
        expected=w>320 or h>320
        assert bool(logs)==expected
        if expected:assert logs==[[2,w,h,320,320]]
        cases.append({'requested':[w,h],'maximum':[320,320],'logged_over_limit':bool(logs),'dimension_memory_unchanged':True,'native_vector_accesses':len(calls)})
    return {'controller_sha256':CTL,'entry':'0xaae1a8','comparison':'0xaae078','cases':cases,'callbacks':'logger only; native vector accessor executed','conclusion':'HU check logs width/height overflow, returns without changing dimensions; no scaling or crop implemented here','receiver_acceptance_proven':False,'vehicle_contact':False}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('controller',type=Path)
    print(json.dumps(verify(p.parse_args().controller),indent=2))
