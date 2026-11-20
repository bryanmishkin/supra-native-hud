#!/usr/bin/env python3
"""Bounded captured ARM model40 writer parity; no receiver/display claim."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import *
from ric_road_list import encode

def verify(path):
 results=[]
 for rows in [[],[[0x1000008]],[[0x1000008,0x1000009]],[[0x1000008],[0x1000009]]]:
  c=cpu_for(path,CTL);obj=BASE+0x1000;stream=BASE+0x2000;buf=BASE+0x8000;entries=BASE+0x3000
  c.mem_write(obj,struct.pack('<IIIIIIII',0x27000004,40,0,0,0,entries,entries+24*len(rows),entries+24*len(rows)))
  for i,ids in enumerate(rows):
   data=BASE+0x4000+i*0x100
   c.mem_write(entries+i*24,struct.pack('<IIIIII',0,data,data+4*len(ids),data+4*len(ids),0,0))
   c.mem_write(data,b''.join(struct.pack('<I',x) for x in ids))
  c.mem_write(stream,struct.pack('<II',buf,buf));calls=[]
  def hook(uc,a,size,u):
   if a==0x127508:
    uc.mem_write(uc.reg_read(UC_ARM_REG_R0),struct.pack('<II',uc.reg_read(UC_ARM_REG_R1),uc.reg_read(UC_ARM_REG_R2)));calls.append('snapshot')
   elif a==0x12a604:
    st,src,n=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
    if n>4096:raise ValueError('Unbounded write')
    cur=struct.unpack('<I',uc.mem_read(st+4,4))[0];uc.mem_write(cur,bytes(uc.mem_read(src,n)));word(uc,st+4,cur+n);uc.reg_write(UC_ARM_REG_R0,n);calls.append('stream-write')
   else:return
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  c.hook_add(UC_HOOK_CODE,hook);c.reg_write(UC_ARM_REG_R0,stream);c.reg_write(UC_ARM_REG_R1,obj);c.reg_write(UC_ARM_REG_LR,BASE)
  try:c.emu_start(0xbbcd70,BASE,count=100000)
  except Exception as e:raise RuntimeError(f'PC {c.reg_read(UC_ARM_REG_PC):x}: {e}') from e
  assert c.reg_read(UC_ARM_REG_PC)==BASE
  end=struct.unpack('<I',c.mem_read(stream+4,4))[0];got=bytes(c.mem_read(buf,end-buf))
  expected=encode(dict(handle=200,model_id=0x27000004,road_type=0,alignment=0,entries=[dict(resources=x,trailing_bytes=[0,0]) for x in rows]))[17:]
  assert got==expected,(got.hex(),expected.hex())
  results.append(dict(rows=rows,wire_hex=got.hex(),match=True,callbacks=calls))
 return dict(sha256=CTL,entry='0xbbcd70',cases=results,limitation='Native model writer; only stream snapshot and bounded raw-write callbacks intercepted. Receiver acceptance/layout not proven.',vehicle_contact=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('controller',type=Path);print(json.dumps(verify(p.parse_args().controller),indent=2))
