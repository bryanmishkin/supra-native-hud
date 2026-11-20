#!/usr/bin/env python3
"""Native type30 absent-resource conversion; no synthetic counter mapping."""
import argparse,json,struct
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--controller',type=Path,required=True);a=p.parse_args();rows=[]
for comm in (0,1):
 c=cpu_for(a.controller,CTL);sender=BASE+0x1000;model=BASE+0x2000;store=BASE+0x4000;sp=BASE+0xd000
 word(c,sender+0x18,store);word(c,sender+0x20,comm);word(c,model+0x24,0xffffffff)
 c.reg_write(UC_ARM_REG_R4,sender);c.reg_write(UC_ARM_REG_R6,model);c.reg_write(UC_ARM_REG_SP,sp)
 c.emu_start(0xab511c,0xab514c,count=5000)
 got=struct.unpack('<I',c.mem_read(sp+0x8c,4))[0];assert got==0xffffffff
 rows.append(dict(comm_type=comm,original_id='0xffffffff',converted_wire_member=hex(got)))
print(json.dumps(dict(cases=rows,intercepts=[],native_calls=['0xaad7f0','0xa3a86c','0xa3a7a8','0xa3a69c'],limitation='Synthetic empty native resource stores, matching prior proof that absent ID is rejected before insertion. Does not emulate receiver or establish position-control removal.'),indent=2))
