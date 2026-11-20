#!/usr/bin/env python3
"""Execute captured ARM alignment-label selection; no vehicle or receiver emulation."""
import argparse,json
from pathlib import Path
from verify_pip_binding_records import cpu_for,BASE,CTL
from unicorn.arm_const import UC_ARM_REG_R4,UC_ARM_REG_R12,UC_ARM_REG_PC

def verify(path):
    rows=[]
    for value,label in [(0,'Left'),(1,'Right')]:
        c=cpu_for(path,CTL)
        c.reg_write(UC_ARM_REG_R4,BASE+0x1000)
        c.mem_write(BASE+0x1025,bytes([value]))
        c.emu_start(0xa47434,0xa47450,count=20)
        assert c.reg_read(UC_ARM_REG_PC)==0xa47450
        address=c.reg_read(UC_ARM_REG_R12)
        actual=bytes(c.mem_read(address,16)).split(b'\0')[0].decode()
        assert actual==label
        rows.append(dict(value=value,label=actual,string_address=hex(address)))
    return dict(binary_sha256=CTL,block=['0xa47434','0xa47450'],intercepts=0,cases=rows,
                limitation='Producer names its alignment selector; receiver physical effect is not established.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('controller',type=Path)
    print(json.dumps(verify(p.parse_args().controller),indent=2))
