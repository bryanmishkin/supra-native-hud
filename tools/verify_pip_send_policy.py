import sys,json,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--controller',required=True,type=Path);p.add_argument('--tools-dir',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();sys.path.insert(0,str(a.tools_dir))
from verify_pip_binding_records import *
results=[]
for flag in [0,1]:
 c=cpu_for(a.controller,CTL);sender=BASE+0x1000;config=BASE+0x2000;word(c,sender+0x68,config);c.mem_write(config+0x290,bytes([flag]));c.reg_write(UC_ARM_REG_R4,sender);c.reg_write(UC_ARM_REG_R1,0x2000001);got=[]
 def stop(cpu,addr,size,user):
  if addr in [0xab0924,0xa8fdc0]:
   got.append({'target':hex(addr),'r0':hex(cpu.reg_read(UC_ARM_REG_R0)),'r1':hex(cpu.reg_read(UC_ARM_REG_R1)),'r2':cpu.reg_read(UC_ARM_REG_R2)});cpu.emu_stop()
 c.hook_add(UC_HOOK_CODE,stop);c.emu_start(0xa88a20,BASE,count=30)
 assert len(got)==1 and got[0]['target']==('0xab0924' if flag==0 else '0xa8fdc0')
 results.append({'config_byte_0x290':flag,'selected_call':got[0]})
print(json.dumps({'sha256':CTL,'start':'0xa88a20','cases':results,'external_functions_executed':0,'limitation':'Native selection branch only. Does not prove captured runtime config or receiver existence state.'},indent=2))
