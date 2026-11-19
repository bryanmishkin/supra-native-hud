#!/usr/bin/env python3
"""Differential execution of complete native junction/intersection metadata setup."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import cpu_for,word,NAV,BASE
from pip_metadata_record import build_record
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

def verify(path):
 cases=[]
 for label,start,stop,offset in [('junction',0x7ee4f4,0x7ee5c8,0x1b0),('intersection',0x7f63cc,0x7f6494,0xa0)]:
  c=cpu_for(path,NAV)
  owner,context,maneuver,style,descriptor,head,node,target,stack=[BASE+x for x in (0x1000,0x2000,0x3000,0x4000,0x5000,0x6000,0x6100,0x7000,0xe000)]
  def hook(uc,address,size,user):
   if address==0x7de388:
    # The current-maneuver lookup is an explicit input boundary. No registry
    # admission, object ownership, renderer or receiver is simulated.
    uc.reg_write(UC_ARM_REG_R0,maneuver)
   elif address==0x105d44:
    x=uc.reg_read(UC_ARM_REG_R0);d=uc.reg_read(UC_ARM_REG_R1)
    assert d==1000 and x<0x80000000
    uc.reg_write(UC_ARM_REG_R0,x//d)
   elif address==0x105d20:
    dst,src,n=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
    assert dst==target+0x14 and src==stack+0x10 and n==84
    uc.mem_write(dst,bytes(uc.mem_read(src,n)))
   else:return
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  c.hook_add(UC_HOOK_CODE,hook)
  for typ in [4402,5402,8301,8402]:
   for flag in [False,True]:
    for option in [0,9]:
     c.mem_write(BASE+0x1000,bytes(0xe000));word(c,owner+offset,target)
     word(c,context,style);word(c,context+0x20,typ);c.mem_write(context+0x54,struct.pack('<H',0x1234))
     word(c,style+0x84,descriptor);word(c,descriptor+0x10,0 if flag else 1)
     word(c,maneuver+0x200,0x0f000004);word(c,maneuver+0x1ec,head)
     word(c,head+4,node);c.mem_write(head+0x15,b'\1')
     word(c,node,head);word(c,node+8,head);word(c,node+0xc,0);word(c,node+0x10,option)
     c.reg_write(UC_ARM_REG_R4,owner);c.reg_write(UC_ARM_REG_R5,context);c.reg_write(UC_ARM_REG_R6,maneuver);c.reg_write(UC_ARM_REG_SP,stack)
     c.emu_start(start,stop,count=1500)
     assert c.reg_read(UC_ARM_REG_PC)==stop
     observed=bytes(c.mem_read(target+0x14,84));expected=build_record(typ,0x1234,0x0f000004,flag,option)
     assert observed==expected,(label,typ,flag,option,observed.hex(),expected.hex())
     cases.append({'renderer':label,'guidance_type':typ,'style_flag':flag,'option_zero':option,'record_hex':observed.hex(),'match':True})
 return {'binary_sha256':NAV,'cases':cases,'intercepts':['current-maneuver lookup input (junction only)','signed division ABI','memcpy ABI'],
  'executed':'Native record initializer, style/context accessors, option-map lookup, field writes, record setter.',
  'not_executed':'GL drawing, framebuffer conversion, physical output or receiver.', 'vehicle_contact':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('nav',type=Path);a=p.parse_args();print(json.dumps(verify(a.nav),indent=2))
