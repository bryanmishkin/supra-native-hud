#!/usr/bin/env python3
"""Offline native branch-high payload conformance; no vehicle operations."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import *
from ric_branch_high import encode

def verify(path):
 rows=[]
 for picture in (0x01000008,0x01000009,0xffffffff):
  c=cpu_for(path,CTL);obj=BASE+0x1000;stream=BASE+0x2000;buf=BASE+0x4000;calls=[]
  c.mem_write(obj,struct.pack('<IIII',0x03000004,3,3,picture));word(c,stream,buf);word(c,stream+4,buf)
  def hook(uc,a,n,u):
   if a==0x127508:
    dst=uc.reg_read(UC_ARM_REG_R0);uc.mem_write(dst,struct.pack('<II',uc.reg_read(UC_ARM_REG_R1),uc.reg_read(UC_ARM_REG_R2)));calls.append('stream-snapshot')
   elif a==0x12a604:
    st,src,size=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)];assert size in (1,4)
    cur=struct.unpack('<I',uc.mem_read(st+4,4))[0];assert buf<=cur<=buf+16
    uc.mem_write(cur,bytes(uc.mem_read(src,size)));word(uc,st+4,cur+size);uc.reg_write(UC_ARM_REG_R0,size);calls.append('stream-write')
   else:return
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  c.hook_add(UC_HOOK_CODE,hook);c.reg_write(UC_ARM_REG_R0,stream);c.reg_write(UC_ARM_REG_R1,obj);c.reg_write(UC_ARM_REG_LR,BASE)
  c.emu_start(0xbae3c0,BASE,count=4000);assert c.reg_read(UC_ARM_REG_PC)==BASE
  end=struct.unpack('<I',c.mem_read(stream+4,4))[0];got=bytes(c.mem_read(buf,end-buf));expected=encode(200,0x03000004,3,3,picture)[17:]
  assert got==expected and len(got)==10
  rows.append(dict(picture=hex(picture),payload=got.hex(),native_match=True,imports=calls))
 return dict(binary_sha256=CTL,entry='0xbae3c0',cases=rows,scope='Actual tuple/enum/integer writers; stream snapshot/write supplied. No receiver or visible extent proof.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('controller',type=Path);a=p.parse_args();print(json.dumps(verify(a.controller),indent=2))
