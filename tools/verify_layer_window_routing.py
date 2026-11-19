#!/usr/bin/env python3
"""Execute captured LayerManager surface lookup; no Screen/window operations."""
import argparse,json,struct
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--layer',type=Path,required=True);a=p.parse_args()
SHA='8a85b61891f0f96f4927b1eccefaa5d31821c7eb9eaf317484f723ac880256b1';rows=[]
for ident in [1056,1024,1025,268444457]:
 c=cpu_for(a.layer,SHA);c.reg_write(UC_ARM_REG_R7,ident);c.emu_start(0x128de8,0x128dec,count=1);surface=c.reg_read(UC_ARM_REG_R4)
 c.emu_start(0x128e9c,0x128ea0,count=1) # loads exact native table
 c.reg_write(UC_ARM_REG_LR,BASE+0x3000);c.reg_write(UC_ARM_REG_R2,0xefa4)
 c.emu_start(0x128eb8,0x128ef8,count=2000)
 idx=c.reg_read(UC_ARM_REG_R10);idx=idx if idx<0x80000000 else idx-0x100000000
 assert idx==({1056:1,1024:0,1025:1}.get(surface,-1))
 rows.append({'window_numeric_id':ident,'surface_id':surface,'table_display_index':idx,'unknown_id_high_nibble':ident>>28})
c=cpu_for(a.layer,SHA);ctx=BASE+0x1000;sp=BASE+0xc000;c.reg_write(UC_ARM_REG_SP,sp);c.reg_write(UC_ARM_REG_R6,ctx);c.reg_write(UC_ARM_REG_R7,268444457);c.reg_write(UC_ARM_REG_R10,0xffffffff);word(c,ctx+0x28,2)
c.emu_start(0x128ef8,0x128f5c,count=100)
assert c.reg_read(UC_ARM_REG_R10)==1
assert bytes(c.mem_read(sp+0x24,4))==bytes(4)
fallback={'display_index_from_high_nibble':1,'screen_display_pointer':0,'skips_display_setter':True}
print(json.dumps({'sha256':SHA,'table':'0x15340c','native_lookup':'0x128eb8..0x128ef4','cases':rows,'unknown_surface_fallback':fallback,'intercepts':[],'limitation':'Proves exact table selection and high-nibble stripping. Physical receiver/display naming remains outside this routine; actual Screen calls not executed.'},indent=2))
