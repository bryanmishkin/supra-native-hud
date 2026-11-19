#!/usr/bin/env python3
"""Execute the captured producer's phase predicate; no vehicle or receiver model."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import cpu_for,CTL,BASE,UC_ARM_REG_R0,UC_ARM_REG_R4

def verify(path):
    results=[]
    for phase in (-1,0,1,2,3,4,5,6):
        cpu=cpu_for(path,CTL);ptr=BASE+0x1000
        cpu.mem_write(ptr,struct.pack('<i',phase));cpu.reg_write(UC_ARM_REG_R0,ptr)
        cpu.emu_start(0xa782c4,0xa782d4,count=8)
        got=cpu.reg_read(UC_ARM_REG_R4)
        assert got==int(phase>2)
        results.append({'phase':phase,'is_main_phase':bool(got)})
    return {'binary_sha256':CTL,'entry':'0xa782c4','end':'0xa782d4','imports_intercepted':0,
        'results':results,'scope':'Predicate inside controller isMainPhaseForPIP. Does not execute cluster receiver, prove phase-index names, or change B009 selection.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('controller',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.controller),indent=2))
