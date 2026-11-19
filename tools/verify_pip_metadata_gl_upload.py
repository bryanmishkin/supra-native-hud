#!/usr/bin/env python3
"""Execute captured texture-upload setup up to GL; never emulate its framebuffer."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import cpu_for,word,NAV,BASE
from pip_metadata_record import build_cpu_upload
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

def verify(path):
 rows=[]
 for typ in [4402,8301,8402]:
  c=cpu_for(path,NAV);manager,image,rect,pixels= [BASE+x for x in (0x1000,0x2000,0x3000,0x4000)]
  word(c,manager,BASE+0x5000);word(c,image+8,0)
  c.mem_write(rect,struct.pack('<IIII',0,0,21,1))
  upload=build_cpu_upload(typ,0x1234,0x0f000004,True)
  c.mem_write(pixels,upload);calls=[]
  def hook(uc,address,size,user):
   if address in (0x8ae2c0,0x8ad088):pass # image binding/state boundary, not simulated GL state
   elif address==0x1064b8:
    args=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
    args+=list(struct.unpack('<IIIII',bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_SP),20))))
    calls.append(args)
    assert args==[0xde1,0,0,0,21,1,0x1908,0x1401,pixels]
    assert bytes(uc.mem_read(args[-1],84))==upload
   elif address==0x106974:uc.reg_write(UC_ARM_REG_R0,0)
   else:return
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  c.hook_add(UC_HOOK_CODE,hook)
  for r,v in [(UC_ARM_REG_R0,manager),(UC_ARM_REG_R1,image),(UC_ARM_REG_R2,rect),(UC_ARM_REG_R3,pixels),(UC_ARM_REG_LR,BASE)]:c.reg_write(r,v)
  c.emu_start(0x8b1b7c,BASE,count=500)
  assert c.reg_read(UC_ARM_REG_PC)==BASE and len(calls)==1
  rows.append({'guidance_type':typ,'width':21,'height':1,'format':'GL_RGBA (0x1908)','type':'GL_UNSIGNED_BYTE (0x1401)','upload_hex':upload.hex(),'native_argument_match':True})
 return {'binary_sha256':NAV,'cases':rows,'intercepts':['texture-binding/state helpers','glTexSubImage2D argument observer','glGetError returns zero'],
 'conclusion':'The captured NGE implementation uploads rotated metadata as RGBA bytes; the VG diagnostic name is not the actual upload API.',
 'framebuffer_rendered':False,'receiver_binding_proven':False,'vehicle_contact':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('nav',type=Path);a=p.parse_args();print(json.dumps(verify(a.nav),indent=2))
