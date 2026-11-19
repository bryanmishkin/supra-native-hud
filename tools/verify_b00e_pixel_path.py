#!/usr/bin/env python3
"""Execute captured HMI bitmap dimension/ID blocks, never receiver or vehicle code.
Requires the exact privately retained ELF. Helper boundaries are explicit below.
"""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import cpu_for,word,BASE
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R11,UC_ARM_REG_LR,UC_ARM_REG_PC
from canvas_geometry import SIZES
HMI='fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935'

def verify(path):
 results=[]
 for width,height in (*SIZES,(0,36),(36,0),(129,128),(128,129)):
  c=cpu_for(path,HMI);owner=BASE+0x1000;fp=BASE+0x8000
  c.reg_write(UC_ARM_REG_R4,owner);c.reg_write(UC_ARM_REG_R11,fp)
  c.mem_write(fp-0x64,struct.pack('<HH',width,height))
  word(c,owner+0x1c,BASE+0x2000)
  word(c,owner+0x5c,0x01000008)
  word(c,owner+0x78,0x01000000);word(c,owner+0x7c,0x0100000a)
  submissions=[];rejected=[]
  def hook(uc,address,size,user):
   if address==0x251e6b8:
    uc.mem_write(uc.reg_read(UC_ARM_REG_R1),struct.pack('<H',128))
    uc.mem_write(uc.reg_read(UC_ARM_REG_R2),struct.pack('<H',128))
   elif address==0x82daec:pass # C++ byte-vector copy boundary; not tested here.
   elif address==0x2592b44:
    submissions.append({'resource_id':hex(uc.reg_read(UC_ARM_REG_R1)),
      'dimensions':list(struct.unpack('<HH',bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R2),4))))})
   elif address==0x25932b8:
    rejected.append(True);uc.emu_stop();return
   else:return
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  c.hook_add(UC_HOOK_CODE,hook)
  c.emu_start(0x2593194,0x2593234,count=120)
  expected=0<width<=128 and 0<height<=128
  if expected:
   assert submissions==[{'resource_id':'0x1000009','dimensions':[width,height]}] and not rejected
  else:assert rejected and not submissions
  results.append({'input':[width,height],'factory_dimension_branch_accepts':expected,'submission':submissions})
 return {'binary_sha256':HMI,'executed_region':['0x2593194','0x2593234'],
  'cases':results,'helper_boundaries':{'0x251e6b8':'supplied measured 128x128 configuration',
   '0x82daec':'C++ vector copy skipped','0x2592b44':'captured submitted ID and dimensions; resource sender not executed'},
  'receiver_rendering_verified':False,'vehicle_contact':False,
  'conclusion':'Factory producer accepts independent width/height within measured bounds; preserves dimensions into bitmap submission.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('hmi',type=Path);a=p.parse_args()
 print(json.dumps(verify(a.hmi),indent=2))
