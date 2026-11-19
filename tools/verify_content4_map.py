"""Execute actual SetContent variant4 map insertion with an existing bounded node."""
import argparse,json
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--nav',type=Path,required=True);a=p.parse_args();rows=[]
for unused in [0,0xdeadbeef]:
 c=cpu_for(a.nav,NAV);owner=BASE+0x1000;payload=BASE+0x2000;sentinel=BASE+0x3000;node=BASE+0x3100;items=BASE+0x4000
 word(c,owner+0x1d4,sentinel);word(c,sentinel+4,node);c.mem_write(sentinel+0x21,b'\x01')
 for off,v in [(0,sentinel),(8,sentinel),(12,1234),(0x14,items),(0x18,items),(0x1c,items+16)]:word(c,node+off,v)
 for off,v in [(0,0x11223344),(4,unused),(8,1234)]:word(c,payload+off,v)
 c.reg_write(UC_ARM_REG_R0,owner);c.reg_write(UC_ARM_REG_R1,payload);c.reg_write(UC_ARM_REG_LR,BASE+0xf100)
 c.emu_start(0x86ecc0,BASE+0xf100,count=500)
 value=int.from_bytes(c.mem_read(items,4),'little');end=int.from_bytes(c.mem_read(node+0x18,4),'little');flags=int.from_bytes(c.mem_read(owner+0x1cc,4),'little')
 assert value==0x11223344 and end==items+4 and flags==0x10
 rows.append({'payload_words':[0x11223344,unused,1234],'map_key':1234,'appended_u32':value,'dirty_flags':flags})
print(json.dumps({'sha256':NAV,'entry':'0x86ecc0','cases':rows,'intercepts':[],'limitation':'Existing-node path only, bounded synthetic map with actual ARM append; no image interpretation, transport or renderer execution.'},indent=2))
