#!/usr/bin/env python3
"""Bounded native property dispatch, not a Screen/server simulator."""
import argparse,hashlib,json
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--nav',type=Path,required=True);p.add_argument('--kd',type=Path,required=True);a=p.parse_args()
KD_SHA='0143ec0ffd77a9712e9944275da3ea5933d3482b3441fad9859612942eef6959';rows=[]
for screen in [0,1,2]:
 c=cpu_for(a.nav,NAV);word(c,BASE+0xf000+0x20,screen);word(c,BASE+0x1000+8,BASE+0x2000);c.reg_write(UC_ARM_REG_R4,BASE+0x1000);c.reg_write(UC_ARM_REG_R6,BASE+0xf020)
 stopped=[]
 def hook(cpu,addr,size,_):
  if addr in [0x106674,0x8830f8]:stopped.append(addr);cpu.emu_stop()
 c.hook_add(UC_HOOK_CODE,hook);c.emu_start(0x8830ac,0,count=100)
 assert stopped==[0x8830f8 if screen==0 else 0x106674]
 rows.append({'screen_number':screen,'calls_display_setter':screen!=0,'property':c.reg_read(UC_ARM_REG_R1) if screen else None})
c=cpu_for(a.kd,KD_SHA);c.reg_write(UC_ARM_REG_R5,BASE+0x1000);c.reg_write(UC_ARM_REG_R4,0x3eb);c.emu_start(0x4364,0x4504,count=100);assert c.reg_read(UC_ARM_REG_PC)==0x4504
print(json.dumps({'nav_sha256':NAV,'kd_sha256':KD_SHA,'screen_number_branch':rows,'display_property_0x3eb_dispatch':'invalid-property branch0x4504 before any Screen call','intercepts':[],'limitation':'Native branch execution only; no Screen service/device execution. This captured KD integer setter rejects property1003. Factory constructor supplies caption1056 and omitsScreenNumber; its defaultscreenselection stillbelongs toScreen/LayerManager.'},indent=2))
