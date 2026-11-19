"""Native subscription-control arguments; offline, no broker or sockets."""
import argparse,json
from verify_pip_binding_records import *
from verify_dsi_frame_equivalence import MOCCA,COLIBRY
p=argparse.ArgumentParser();p.add_argument('--mocca',required=True,type=Path);p.add_argument('--colibry',required=True,type=Path);a=p.parse_args();rows=[]
for entry,event,sequence,expected in [(0xb12cc,0x80000004,37,0x106),(0xb1224,0,37,0x107)]:
 c=cpu_for(a.mocca,MOCCA);obj=BASE+0x1000;vt=BASE+0x2000;target=BASE+0xe000;word(c,obj,vt);word(c,vt+0x20,target);c.mem_write(obj+0x50,b'\1')
 c.reg_write(UC_ARM_REG_R0,obj);c.reg_write(UC_ARM_REG_R1,event if entry==0xb12cc else sequence);c.reg_write(UC_ARM_REG_R2,sequence);c.reg_write(UC_ARM_REG_LR,BASE+0xf100);seen=[]
 def hook(cpu,address,size,data):
  if address==target:
   seen.append([cpu.reg_read(r) for r in (UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 c.hook_add(UC_HOOK_CODE,hook);c.emu_start(entry,BASE+0xf100,count=300);assert seen==[[expected,event,sequence]]
 rows.append({'native_entry':hex(entry),'control_type':hex(expected),'event':hex(event),'owned_sequence':sequence,'intercept':'downstream virtual send only'})
for entry,expected in [(0x2bdc0,0x101),(0x2bcf4,0x102)]:
 c=cpu_for(a.colibry,COLIBRY);obj=BASE+0x1000;stream=BASE+0x2000;c.reg_write(UC_ARM_REG_R4,obj);c.reg_write(UC_ARM_REG_R6,stream);c.reg_write(UC_ARM_REG_R8,0x80000004);seen=[]
 def hook2(cpu,address,size,data):
  if address==0x250f8:
   sp=cpu.reg_read(UC_ARM_REG_SP);args=[int.from_bytes(cpu.mem_read(sp+i*4,4),'little') for i in range(6)];seen.append(args);cpu.emu_stop()
 c.hook_add(UC_HOOK_CODE,hook2);c.emu_start(entry,BASE+0xf100,count=100);assert seen[0][0]==expected and seen[0][2]==0x80000004 and seen[0][5]==0
 rows.append({'native_entry':hex(entry),'convenience_type':hex(expected),'event':hex(seen[0][2]),'hardcoded_sequence':seen[0][5],'intercept':'constructor boundary; bounded setup block after logging'})
print(json.dumps({'mocca_sha256':MOCCA,'colibry_sha256':COLIBRY,'cases':rows,'limitation':'Native argument dataflow only. Explicit stream constructor needed for registry105/106; no live registration, subscription or detach performed.'},indent=2))
