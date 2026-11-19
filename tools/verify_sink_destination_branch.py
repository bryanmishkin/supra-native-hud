#!/usr/bin/env python3
"""Execute captured destination decision without transport or vehicle access."""
import argparse,json
from unicorn import UC_HOOK_CODE
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--controller',type=Path,required=True);a=p.parse_args()
rows=[]
for cached in (0,1):
 for selection in (0,1):
  c=cpu_for(a.controller,CTL);owner=BASE+0x1000;manager=BASE+0x2000;event=BASE+0x3000;payload=BASE+0x4000
  word(c,owner+0x14,manager);word(c,event+0x10,0);word(c,event+24,payload)
  c.mem_write(manager+24,bytes([cached]));c.mem_write(payload+24,bytes([selection]))
  c.reg_write(UC_ARM_REG_R4,owner);c.reg_write(UC_ARM_REG_R7,event)
  hits=[]
  def stop(cpu,address,size,data):
   if address in (0xa7a268,0xa7a2ac,0xa7a2dc):hits.append(address);cpu.emu_stop()
  c.hook_add(UC_HOOK_CODE,stop);c.emu_start(0xa7a228,0xa7a55c,count=100)
  new=c.mem_read(manager+24,1)[0];assert new==(selection==0)
  rows.append(dict(cached_hud=cached,incoming_selection=selection,new_hud=new,stop_address=hex(hits[0])))
print(json.dumps(dict(cases=rows,intercepts=[],limitations='Executes native notification branch; does not fabricate receiver selection or execute remote routing.'),indent=2))
