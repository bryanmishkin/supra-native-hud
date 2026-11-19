"""Verify indexed key hashing against actual captured ARM; libc formatting intercepted."""
import argparse,json
from style_xpd import guiding_view_keys
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--nav',required=True,type=Path);a=p.parse_args();rows=[]
for view in [8301,8402]:
 c=cpu_for(a.nav,NAV);out=BASE+0x1000;desc=BASE+0x2000;string=BASE+0x3000;c.mem_write(string,b'guiding.*.viewStyle\0')
 for off,v in [(0,0),(4,string),(8,view),(12,2)]:word(c,desc+off,v)
 c.reg_write(UC_ARM_REG_R0,out);c.reg_write(UC_ARM_REG_R1,desc);c.reg_write(UC_ARM_REG_LR,BASE+0xf100);calls=[]
 def hook(cpu,address,size,data):
  if address==0x106470:
   cpu.mem_write(cpu.reg_read(UC_ARM_REG_R0),bytes(cpu.reg_read(UC_ARM_REG_R2)));calls.append('memset')
  elif address==0x10608c:
   value=cpu.reg_read(UC_ARM_REG_R3);text=str(value if value<0x80000000 else value-0x100000000).encode();cpu.mem_write(cpu.reg_read(UC_ARM_REG_R0),text+b'\0');cpu.reg_write(UC_ARM_REG_R0,len(text));calls.append('snprintf decimal')
  else:return
  cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 c.hook_add(UC_HOOK_CODE,hook);c.emu_start(0x636f0c,BASE+0xf100,count=3000)
 count=int.from_bytes(c.mem_read(out,4),'little');values=[int.from_bytes(c.mem_read(out+4+i*4,4),'little') for i in range(count)];assert values==guiding_view_keys(view)
 rows.append({'view_id':view,'components':['guiding','*','viewStyle'+str(view)],'hashes':values,'intercepts':calls})
print(json.dumps({'native_sha256':NAV,'cases':rows,'limitation':'Native hash algorithm verified; libc memset and decimal formatter intercepted, no style database or renderer activation implied.'},indent=2))
