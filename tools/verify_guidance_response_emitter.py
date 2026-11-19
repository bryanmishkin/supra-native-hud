"""Verify native response payload selection; framework allocation/dispatch intercepted."""
import argparse,json
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--nav',required=True,type=Path);a=p.parse_args();rows=[]
for status in [0,2]:
 c=cpu_for(a.nav,NAV);session=BASE+0x1000;result=BASE+0x1004;event=BASE+0x2000;stub=BASE+0x3000;record=BASE+0x4000
 word(c,session,73);word(c,result,status)
 for reg,v in [(UC_ARM_REG_R0,stub),(UC_ARM_REG_R1,session),(UC_ARM_REG_R2,result),(UC_ARM_REG_LR,BASE+0xf100)]:c.reg_write(reg,v)
 calls=[]
 def hook(cpu,address,size,data):
  returns={0x4b58f0:0,0x4b6cf4:37,0x16e7dc:record,0x111d70:event,0x1bd1bc:event}
  if address in returns:
   calls.append(hex(address));cpu.reg_write(UC_ARM_REG_R0,returns[address]);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
  elif address==0x4b6e70:
   assert cpu.reg_read(UC_ARM_REG_R1)==37 and cpu.reg_read(UC_ARM_REG_R2)==event
   cpu.reg_write(UC_ARM_REG_PC,BASE+0xf100)
 c.hook_add(UC_HOOK_CODE,hook);c.emu_start(0x5872bc,BASE+0xf100,count=500)
 payload=bytes(c.mem_read(event+0x50,8));assert payload== (73).to_bytes(4,'little')+status.to_bytes(4,'little')
 rows.append({'session':73,'result':status,'framework_request_token':37,'native_payload_hex':payload.hex(),'intercepted_calls':calls})
print(json.dumps({'sha256':NAV,'entry':'0x5872bc','cases':rows,'limitation':'Native payload copy verified; framework allocation/request lookup/dispatch intercepted. Does not exercise transport or establish rendering success.'},indent=2))
