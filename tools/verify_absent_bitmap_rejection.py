#!/usr/bin/env python3
"""Execute native bitmap-store absent-ID rejection, without allocation hooks."""
import argparse,json
from unicorn import UC_HOOK_CODE
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--controller',type=Path,required=True);a=p.parse_args();rows=[]
for ident in (0xffffffff,1,0x07000000):
 c=cpu_for(a.controller,CTL);obj=BASE+0x1000;resource=BASE+0x2000;end=BASE+0x3000
 word(c,resource+4,ident);c.reg_write(UC_ARM_REG_R0,obj);c.reg_write(UC_ARM_REG_R1,resource);c.reg_write(UC_ARM_REG_R2,1);c.reg_write(UC_ARM_REG_LR,end)
 hits=[]
 def stop(cpu,address,size,data):
  if address==0xa54a08:hits.append(address);cpu.emu_stop()
 c.hook_add(UC_HOOK_CODE,stop);c.emu_start(0xa5496c,end,count=60)
 rejected=not hits
 assert rejected==(ident==0xffffffff)
 if rejected:assert c.reg_read(UC_ARM_REG_R0)==0
 rows.append(dict(original_id=hex(ident),rejected_before_insertion=rejected,continued_to_validation=bool(hits)))
print(json.dumps(dict(cases=rows,intercepts=[],limitation='Non-absent IDs stop before lookup/insertion and are not declared accepted. Absent ID returns false before any store mutation.'),indent=2))
