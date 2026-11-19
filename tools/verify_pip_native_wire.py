#!/usr/bin/env python3
"""Execute captured HMI PiP serializer offline; not receiver acceptance."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import cpu_for,word,BASE
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_LR,UC_ARM_REG_PC

def verify(p):
 sha='fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935'
 results=[]
 for w,h,depth,packing in [(320,200,0,0),(460,237,0,0),(800,480,0,1),(320,320,1,0)]:
  c=cpu_for(p,sha);obj=BASE+0x1000;stream=BASE+0x2000;dims=BASE+0x3000;buf=BASE+0x8000
  c.mem_write(obj,struct.pack('<IIIIIII',0x02000004,2,dims,dims+4,dims+4,depth,packing));c.mem_write(dims,struct.pack('<HH',w,h));c.mem_write(stream,struct.pack('<II',buf,buf));calls=[]
  def hook(uc,a,size,u):
   if a==0x299bb40:
    dst=uc.reg_read(UC_ARM_REG_R0);uc.mem_write(dst,struct.pack('<II',uc.reg_read(UC_ARM_REG_R1),uc.reg_read(UC_ARM_REG_R2)));uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));calls.append('snapshot')
   elif a==0x299b360:
    st,src,n=[uc.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]];cur=struct.unpack('<I',uc.mem_read(st+4,4))[0]
    if n>1024:raise ValueError('write too large')
    uc.mem_write(cur,bytes(uc.mem_read(src,n)));word(uc,st+4,cur+n);uc.reg_write(UC_ARM_REG_R0,n);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));calls.append('write')
  c.hook_add(UC_HOOK_CODE,hook);c.reg_write(UC_ARM_REG_R0,obj);c.reg_write(UC_ARM_REG_R1,stream);c.reg_write(UC_ARM_REG_LR,BASE)
  try:c.emu_start(0x289e7bc,BASE,count=10000)
  except Exception as e:print(hex(c.reg_read(UC_ARM_REG_PC)),e);raise
  assert c.reg_read(UC_ARM_REG_PC)==BASE
  end=struct.unpack('<I',c.mem_read(stream+4,4))[0];got=bytes(c.mem_read(buf,end-buf));want=struct.pack('>IBHHBB',0x02000004,2,w,h,depth,packing)
  assert got==want
  results.append({'width':w,'height':h,'depth':depth,'packing':packing,'wire_hex':got.hex(),'native_match':True,'calls':calls})
 return {'sha256':sha,'entry':'0x289e7bc','cases':results,'callbacks':'stream snapshot/write only','receiver_acceptance_proven':False,'vehicle_contact':False}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('hmi',type=Path)
 print(json.dumps(verify(p.parse_args().hmi),indent=2))
