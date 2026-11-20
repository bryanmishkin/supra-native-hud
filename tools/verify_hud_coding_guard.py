#!/usr/bin/env python3
"""Bounded native Ethernet-vs-MOST coding branch; no coding writes."""
import argparse,json
from unicorn import UC_HOOK_CODE
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--controller',type=Path,required=True);a=p.parse_args();rows=[]
for coding in (0,1,2,3):
 c=cpu_for(a.controller,CTL);sp=BASE+0xe000;log=BASE+0x1000;word(c,sp+12,log);c.mem_write(log+14,b'\0')
 c.reg_write(UC_ARM_REG_SP,sp);c.reg_write(UC_ARM_REG_R0,coding);hits=[]
 def stop(cpu,addr,size,data):
  if addr in (0x6ddbe0,0x6dde0c):hits.append(addr);cpu.emu_stop()
 c.hook_add(UC_HOOK_CODE,stop);c.emu_start(0x6ddbb0,0x6dde10,count=40)
 assert hits==[0x6dde0c if coding==3 else 0x6ddbe0]
 rows.append(dict(kombi_cic=coding,next_branch=hex(hits[0]),legacy_hud_coding_block_entered=coding!=3))
print(json.dumps(dict(cases=rows,intercepts=[],limitation='Caller supplies coding result; this does not determine the vehicle coding value. Proves native Ethernet branch skips the four legacy HUD flag getters.'),indent=2))
