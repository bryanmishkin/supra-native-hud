#!/usr/bin/env python3
"""Execute HMI bitmap ID cursor and resource-header setters offline."""
import argparse,json,struct
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--hmi',type=Path,required=True);a=p.parse_args();sha='fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935';rows=[]
for current in (0,0x01000000,0x01000008,0x01000009):
 c=cpu_for(a.hmi,sha);obj=BASE+0x1000;inner=BASE+0x2000;value=BASE+0x3000;kind=value+4;sender=BASE+0x4000
 word(c,obj+0x5c,current);word(c,obj+0x78,0x01000000);word(c,obj+0x7c,0x0100000a);c.reg_write(UC_ARM_REG_R4,obj)
 c.emu_start(0x25931dc,0x2593204,count=30);rid=struct.unpack('<I',c.mem_read(obj+0x5c,4))[0]
 assert rid==(current+1 if 0x01000000<=current+1<0x0100000a else 0x01000000)
 word(c,value,rid);word(c,kind,1)
 for entry,r0,r1,r2 in [(0x251e758,sender,rid,0),(0x251e744,sender,1,0),(0x29237d8,inner,value,kind)]:
  c.reg_write(UC_ARM_REG_R0,r0);c.reg_write(UC_ARM_REG_R1,r1);c.reg_write(UC_ARM_REG_R2,r2);c.reg_write(UC_ARM_REG_LR,BASE+0x5000);c.emu_start(entry,BASE+0x5000,count=40)
 outer=struct.unpack('<I',c.mem_read(sender+0x40,4))[0];ir,it=struct.unpack('<II',c.mem_read(inner+4,8));assert outer==ir==rid and it==1
 rows.append(dict(cursor_before=hex(current),returned_resource_id=hex(rid),outer_id=hex(outer),inner_id=hex(ir),resource_type=it))
print(json.dumps(dict(cases=rows,intercepts=[],limitation='Executes cursor/header setters only; does not claim whole provider or receiver emulation, allocation availability, or a fresh instance.'),indent=2))
