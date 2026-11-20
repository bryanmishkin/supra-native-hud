#!/usr/bin/env python3
"""Offline native distance payload conformance; no vehicle operations."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import *


def verify(path):
 rows=[]
 for picture in (461.0,92.0,70.0,69.0,0.0):
  c=cpu_for(path,CTL);obj=BASE+0x1000;stream=BASE+0x2000;buf=BASE+0x4000;calls=[]
  c.mem_write(obj,struct.pack('<IIB',0x1d00001d,29,255));c.mem_write(obj+0x10,struct.pack('<d',picture))
  c.mem_write(obj+0x18,struct.pack('<IIII',0,BASE+0x3000,BASE+0x3005,BASE+0x3005));c.mem_write(BASE+0x3000,bytes.fromhex('2143646464'))
  word(c,obj+0x40,15);word(c,obj+0x44,3);c.mem_write(obj+0x48,struct.pack('<Q',0x10edd));word(c,stream,buf);word(c,stream+4,buf)

  def hook(uc,a,n,u):
   if a==0x127508:
    dst=uc.reg_read(UC_ARM_REG_R0);uc.mem_write(dst,struct.pack('<II',uc.reg_read(UC_ARM_REG_R1),uc.reg_read(UC_ARM_REG_R2)));calls.append('stream-snapshot')
   elif a==0x12a604:
    st,src,size=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)];assert size in (1,2,4,8)
    cur=struct.unpack('<I',uc.mem_read(st+4,4))[0];assert buf<=cur<=buf+128
    uc.mem_write(cur,bytes(uc.mem_read(src,size)));word(uc,st+4,cur+size);uc.reg_write(UC_ARM_REG_R0,size);calls.append('stream-write')
   else:return
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  c.hook_add(UC_HOOK_CODE,hook);c.reg_write(UC_ARM_REG_R0,stream);c.reg_write(UC_ARM_REG_R1,obj);c.reg_write(UC_ARM_REG_LR,BASE)
  c.emu_start(0xbb6970,BASE,count=20000);assert c.reg_read(UC_ARM_REG_PC)==BASE
  end=struct.unpack('<I',c.mem_read(stream+4,4))[0];got=bytes(c.mem_read(buf,end-buf))
  expected=struct.pack('>IBBdI',0x1d00001d,29,255,picture,5)+bytes.fromhex('2143646464')+struct.pack('>I',4)+bytes.fromhex('feff0000')+struct.pack('>BQ',3,0x10edd)
  assert got==expected and len(got)==40

  rows.append(dict(distance=picture,payload=got.hex(),native_match=True,imports=calls))
 return dict(binary_sha256=CTL,entry='0xbb6970',cases=rows,scope='Actual tuple, byte-vector, double, UTF string, enum and u64 writers; only stream snapshot/write supplied. No receiver-stage or visible-output proof.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('controller',type=Path);a=p.parse_args();print(json.dumps(verify(a.controller),indent=2))
