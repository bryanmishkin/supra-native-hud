#!/usr/bin/env python3
"""Observe actual native image draw decisions; no framebuffer/receiver simulation."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import cpu_for,word,NAV,BASE
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

def verify(path):
 rows=[]
 for alpha_enabled,opacity in [(0,255),(1,255),(0,128)]:
  c=cpu_for(path,NAV)
  image,manager=BASE+0x1000,BASE+0x2000
  word(c,image+8,0);c.mem_write(image+0x14,bytes([alpha_enabled]))
  sp=c.reg_read(UC_ARM_REG_SP)
  c.mem_write(sp+0x48,bytes([opacity,255,255,255]))
  for reg,val in [(UC_ARM_REG_R6,image),(UC_ARM_REG_R4,manager),(UC_ARM_REG_R5,manager+0x1a4)]:c.reg_write(reg,val)
  calls={}
  def hook(uc,addr,size,user):
   if addr==0x8adfc8:calls['blend_enabled']=bool(uc.reg_read(UC_ARM_REG_R1))
   elif addr==0x8ae1a8:calls['native_color_bytes']=bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R1),4)).hex()
   elif addr==0x8ae0ac:calls['blend_mode']=uc.reg_read(UC_ARM_REG_R1)
   elif addr==0x8abc60:calls['shader_object']=hex(uc.reg_read(UC_ARM_REG_R1))
   elif addr==0x8ad088:pass
   else:return
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  c.hook_add(UC_HOOK_CODE,hook)
  c.emu_start(0x8b1910,0x8b19cc,count=500)
  assert c.reg_read(UC_ARM_REG_PC)==0x8b19cc
  assert calls['blend_enabled']==bool(alpha_enabled or opacity!=255)
  assert calls['native_color_bytes']==bytes([255 if alpha_enabled else opacity,0,0,0]).hex()
  assert calls['blend_mode']==1 and calls['shader_object']=='0x1df7fa4'
  # Execute the selected color uniform writer, including its alpha-minus-one
  # conversion. Observe only the final GL call, not the arithmetic.
  c=cpu_for(path,NAV)
  c.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20)
  c.reg_write(UC_ARM_REG_FPEXC,0x40000000)
  color=BASE+0x1000
  c.mem_write(color+0xc,bytes.fromhex(calls['native_color_bytes']))
  word(c,color+0x30,7)
  uniforms=[]
  def uniform_hook(uc,addr,size,user):
   if addr==0x106b84:
    raw=b''.join(struct.pack('<I',uc.reg_read(r)) for r in (UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3))
    raw+=bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_SP),4))
    uniforms.append(list(struct.unpack('<4f',raw)))
   elif addr==0x106974:uc.reg_write(UC_ARM_REG_R0,0)
   else:return
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  c.hook_add(UC_HOOK_CODE,uniform_hook)
  c.reg_write(UC_ARM_REG_R0,color);c.reg_write(UC_ARM_REG_LR,BASE)
  c.emu_start(0x8af08c,BASE,count=500)
  assert c.reg_read(UC_ARM_REG_PC)==BASE and len(uniforms)==1
  assert uniforms[0][:3]==[0.,0.,0.]
  if alpha_enabled or opacity==255:assert uniforms[0][3]==0.
  calls['additive_shader_uniform']=uniforms[0]
  rows.append(dict(image_alpha_enabled=alpha_enabled,opacity=opacity,**calls))
 return dict(binary_sha256=NAV,cases=rows,
  native_region='0x8b1910-0x8b19cc',
  intercepts=['state setters observed without applying GL state','shader selection observed','surface state binding'],
  shader_constructor='0x8addc0 associates object 0x1df7fa4 with fragment source 0xa66bc0',
  conclusion='For the metadata image format 0 with alpha disabled and full opacity, native drawing disables blending and selects the image shader. Other alpha/opacity cases enable blending.',
  framebuffer_rendered=False,receiver_binding_proven=False,vehicle_contact=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('nav',type=Path);a=p.parse_args();print(json.dumps(verify(a.nav),indent=2))
