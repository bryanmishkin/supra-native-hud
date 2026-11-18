"""Bounded execution of the captured ID consumer; virtual dependencies are observed boundaries."""
import argparse,struct,json
from pathlib import Path
from verify_pip_binding_records import cpu_for,word,CTL,BASE
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('controller',type=Path)
p=parser.parse_args().controller
results=[]
for label,ids,sessions,jobs in [('both',[17,34],[1,1],[1,1]),('hmi-only',[17,0xffffffff],[1,1],[1,1]),('ic-only',[0xffffffff,34],[1,1],[1,1]),('neither',[0xffffffff]*2,[1,1],[1,1]),('no-sessions',[17,34],[0,0],[1,1]),('no-jobs',[17,34],[1,1],[0,0]),('missing-hmi-job',[17,34],[1,1],[0,1])]:
 c=cpu_for(p,CTL);owner=BASE+0x1000;record=BASE+0x2000;svt=BASE+0x3000;jvt=BASE+0x3100;lookup=BASE+0x6000;setter=BASE+0x6004
 c.mem_write(record,struct.pack('<III',42,*ids));word(c,svt+0x30,lookup);word(c,jvt+0x20,setter)
 for i in range(2):
  s=BASE+0x4000+i*0x100;j=BASE+0x5000+i*0x100
  word(c,owner+0x6c+4*i,s if sessions[i] else 0);word(c,s,svt);word(c,j,jvt)
 calls=[]
 def boundary(cpu,a,size,user):
  if a==lookup:
   i=(cpu.reg_read(UC_ARM_REG_R0)-(BASE+0x4000))//0x100
   assert i in (0,1)
   assert struct.unpack('<I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),4)))[0]==42
   cpu.reg_write(UC_ARM_REG_R0,BASE+0x5000+i*0x100 if jobs[i] else 0)
   cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
  elif a==setter:
   i=(cpu.reg_read(UC_ARM_REG_R0)-(BASE+0x5000))//0x100
   identity=struct.unpack('<I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),4)))[0]
   calls.append([i,identity]);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 c.hook_add(UC_HOOK_CODE,boundary);c.reg_write(UC_ARM_REG_R0,owner);c.reg_write(UC_ARM_REG_R1,record);c.reg_write(UC_ARM_REG_LR,BASE)
 c.emu_start(0xa75104,BASE,count=100)
 assert c.reg_read(UC_ARM_REG_PC)==BASE
 expected=[[i,ids[i]] for i in range(2) if ids[i]!=0xffffffff and sessions[i] and jobs[i]]
 assert calls==expected,(label,calls,expected)
 results.append({'case':label,'setter_calls':calls})
print(json.dumps({'controller_sha256':CTL,'start':'0xa75104','cases':results,'boundaries':'virtual job lookup and setter observed/substituted; not executed','receiver_verified':False,'vehicle_contact':False},indent=2))
