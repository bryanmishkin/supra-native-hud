"""Bounded native unregister command and attachment invalidation proof.
Notification allocation/delivery/destruction are intercepted; this is not a live cleanup test.
"""
import argparse,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--nav',required=True,type=Path);a=p.parse_args()
from verify_pip_binding_records import *
rows=[]
for token in [37,0xffffffff]:
 c=cpu_for(a.nav,NAV);obj=BASE+0x1000;cmd=BASE+0x2000
 c.reg_write(UC_ARM_REG_R0,cmd);c.reg_write(UC_ARM_REG_R1,token)
 c.emu_start(0x60e6b8,0x60e6d4,count=16)
 assert int.from_bytes(c.mem_read(cmd+4,4),'little')==7
 assert int.from_bytes(c.mem_read(cmd+12,4),'little')==token
 word(c,obj+4,token);c.reg_write(UC_ARM_REG_R0,obj);c.reg_write(UC_ARM_REG_R1,0);c.reg_write(UC_ARM_REG_LR,BASE+0xf100)
 calls=[]
 def hook(cpu,address,size,data):
  if address in [0x6162dc,0x61a468,0x610284]:
   event={'address':hex(address)}
   if address==0x61a468:
    payload=cpu.reg_read(UC_ARM_REG_R1);event.update(token=int.from_bytes(cpu.mem_read(payload,4),'little'),enabled=cpu.mem_read(payload+4,1)[0])
   calls.append(event);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 c.hook_add(UC_HOOK_CODE,hook);c.emu_start(0x616300,BASE+0xf100,count=200)
 final=int.from_bytes(c.mem_read(obj+4,4),'little');assert final==0xffffffff
 events=[x for x in calls if x['address']=='0x61a468'];assert len(events)==(token!=0xffffffff)
 if events:assert events[0]['token']==token and events[0]['enabled']==0
 rows.append({'initial_token':token,'final_token':final,'callbacks':calls})
print(json.dumps({'sha256':NAV,'cases':rows,'limitations':'Actual command construction and native attachment-token clearing. Three notification lifecycle helpers intercepted; no receiver delivery, bitmap absence, deferred deletion completion, or vehicle state proven.'},indent=2))
