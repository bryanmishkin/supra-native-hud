#!/usr/bin/env python3
"""Execute native metadata destination-byte assignment in both PiP renderers.
No vehicle calls; verifies a producer field, not the remote receiver meaning.
"""
import argparse,json,struct
from verify_pip_binding_records import cpu_for,word,NAV,BASE
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

def verify(path):
 rows=[]
 for label,start,stop,destoff in [('junction',0x7ee5a0,0x7ee5c4,0x1b0),('intersection',0x7f646c,0x7f6490,0xa0)]:
  cpu=cpu_for(path,NAV);context=BASE+0x1000;owner=BASE+0x2000;stack=BASE+0xe000
  intercepted=[]
  def hook(uc,address,size,user):
   if address==0x105d44:
    a=uc.reg_read(UC_ARM_REG_R0);b=uc.reg_read(UC_ARM_REG_R1)
    if b!=1000:raise AssertionError('Unexpected divisor')
    if a>=0x80000000:a-=1<<32
    quotient=abs(a)//b * (-1 if a<0 else 1)
    uc.reg_write(UC_ARM_REG_R0,quotient&0xffffffff)
    uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));intercepted.append('signed division ABI')
  cpu.hook_add(UC_HOOK_CODE,hook)
  for typ in [4301,4402,5301,5402,7301,7402,8000,8301,8402,8999,9000,9403,11402]:
   cpu.mem_write(stack,bytes(128));word(cpu,context+0x20,typ);word(cpu,owner+destoff,BASE+0x3000)
   cpu.reg_write(UC_ARM_REG_R0,context);cpu.reg_write(UC_ARM_REG_R4,owner);cpu.reg_write(UC_ARM_REG_R5,context);cpu.reg_write(UC_ARM_REG_SP,stack)
   cpu.emu_start(start,stop,count=100)
   assert cpu.reg_read(UC_ARM_REG_PC)==stop
   value=bytes(cpu.mem_read(stack+0x17,1))[0]
   assert value==(0 if typ//1000 & 255==8 else 1)
   rows.append({'renderer':label,'guidance_type':typ,'record_byte_7':value})
 return {'binary_sha256':NAV,'cases':rows,'intercepts':['signed division ABI only; native context getter and compare/store execute'],
 'conclusion':'Both producer paths set record byte7 to zero for type group8, one otherwise (low8 bits of quotient).',
 'receiver_meaning_proven':False,'framebuffer_channel_conversion_proven':False,'vehicle_contact':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('nav',type=Path);a=p.parse_args();print(json.dumps(verify(a.nav),indent=2))
