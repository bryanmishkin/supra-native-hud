"""Verify native displayable unregister request sequence and provider command, offline."""
import argparse,json
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--nav',required=True,type=Path);p.add_argument('--controller',required=True,type=Path);a=p.parse_args()
c=cpu_for(a.controller,CTL);event=BASE+0x2000;stub=BASE+0x3000;calls=[]
c.reg_write(UC_ARM_REG_R0,stub);c.reg_write(UC_ARM_REG_R1,37);c.reg_write(UC_ARM_REG_LR,BASE+0xf100)
def hook(cpu,address,size,data):
 if address==0x129968:value=1
 elif address==0x126c80:
  assert cpu.reg_read(UC_ARM_REG_R1)==37;value=0
 elif address==0xc26e04:value=event
 elif address==0x12a388:
  assert cpu.reg_read(UC_ARM_REG_R1)==event;cpu.reg_write(UC_ARM_REG_PC,BASE+0xf100);return
 else:return
 calls.append(hex(address));cpu.reg_write(UC_ARM_REG_R0,value);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
c.hook_add(UC_HOOK_CODE,hook);c.emu_start(0xc271e0,BASE+0xf100,count=300)
fields={hex(off):int.from_bytes(c.mem_read(event+off,4),'little') for off in [0x38,0x40,0x44]};assert fields=={'0x38':37,'0x40':6,'0x44':0}
n=cpu_for(a.nav,NAV);cmd=BASE+0x1000;n.reg_write(UC_ARM_REG_R0,cmd);n.reg_write(UC_ARM_REG_R1,73);n.reg_write(UC_ARM_REG_LR,BASE+0xf100);n.emu_start(0x60eba4,BASE+0xf100,count=100)
assert int.from_bytes(n.mem_read(cmd+4,4),'little')==2 and int.from_bytes(n.mem_read(cmd+12,4),'little')==73
print(json.dumps({'controller_sha256':CTL,'provider_sha256':NAV,'request_fields':fields,'provider_command':{'opcode':2,'displayable_session':73},'request_intercepts':calls,'provider_constructor_intercepts':[],'limitation':'Request construction and command construction verified separately. Synthetic IDs intentionally differ. Framework maps request sequence to registered provider context; no live correlation or display destruction executed.'},indent=2))
