#!/usr/bin/env python3
"""Native completion copies current received selection, not desired HUD mode."""
import argparse,json
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--controller',type=Path,required=True);a=p.parse_args();rows=[]
for selection in (0,1):
 for status in (0,1):
  c=cpu_for(a.controller,CTL);owner=BASE+0x1000;event=BASE+0x2000;payload=BASE+0x3000;sp=BASE+0xe000
  word(c,owner+0x3c,event);word(c,event+0x10,0);word(c,event+24,payload);c.mem_write(payload+24,bytes([selection]))
  c.reg_write(UC_ARM_REG_R0,owner);c.reg_write(UC_ARM_REG_R1,status);c.reg_write(UC_ARM_REG_SP,sp)
  c.emu_start(0xa79f54,0xa79f8c,count=100)
  body=bytes(c.mem_read(sp+12,2));assert body==bytes([selection,status]);rows.append(dict(received_selection=selection,status=status,completion=body.hex()))
print(json.dumps(dict(cases=rows,intercepts=[],entry='0xa79f54',stop_before_dispatch='0xa79f8c',meaning='First completion byte comes from current received notification payload+0x18. No manager destination read or new selection request occurs in this native block.'),indent=2))
