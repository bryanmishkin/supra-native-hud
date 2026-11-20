#!/usr/bin/env python3
"""Execute native HighGuidingImageInfo type assignment; never sends a model."""
import argparse,json
from verify_pip_binding_records import *
def verify(path):
    cpu=cpu_for(path,CTL);obj=BASE+0x1000
    cpu.reg_write(UC_ARM_REG_R1,obj)
    cpu.emu_start(0xa3fea4,0xa3feac,count=2)
    typ=int.from_bytes(cpu.mem_read(obj+8,4),'little')
    assert typ==50
    return {'binary_sha256':CTL,'entry':'0xa3fea4','model_type':typ,'intercepts':[],
        'sender':'0xab4f80','control_union_tag':5,
        'fields_from_native_sender':['renderInstance','referredManeuverId','imageTarget','imageContentType'],
        'limitation':'Only model type assignment is executed. Field labels are from the native sender trace. No receiver capability or destination request proven.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('controller',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.controller),indent=2))
