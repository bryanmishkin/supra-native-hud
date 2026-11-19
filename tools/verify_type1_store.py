"""Bounded captured ARM store proof; OS mutex/memcpy imports modeled explicitly."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import *
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--nav',type=Path,required=True);p=parser.parse_args().nav
results=[]
for state,capacity,lock_rc,label in [(0xfffffffe,36,0,'free'),(7,36,0,'busy'),(0xfffffffe,35,0,'undersized'),(0xfffffffe,36,16,'lock-failed')]:
 c=cpu_for(p,NAV);obj=BASE+0x100;handle=BASE+0x200;mapping=BASE+0x300;source=BASE+0x400;payload=bytes(range(24));calls=[]
 word(c,obj+4,handle);word(c,obj+8,capacity);word(c,handle,mapping);word(c,mapping+8,state);c.mem_write(mapping+12,b'\xa5'*32);c.mem_write(source,payload)
 # Diagnostic flags remain zero; failure diagnostics are skipped, not part of storage semantics.
 def hook(uc,a,n,user):
  if a in [0x105d08,0x1059cc,0x105d20,0x11533c]:
   calls.append(hex(a))
   if a==0x105d20:
    dst=uc.reg_read(UC_ARM_REG_R0);src=uc.reg_read(UC_ARM_REG_R1);size=uc.reg_read(UC_ARM_REG_R2);assert size==24;uc.mem_write(dst,bytes(uc.mem_read(src,size)))
   elif a==0x105d08:uc.reg_write(UC_ARM_REG_R0,lock_rc)
   elif a==0x1059cc:uc.reg_write(UC_ARM_REG_R0,0)
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
 c.hook_add(UC_HOOK_CODE,hook)
 for reg,val in [(UC_ARM_REG_R0,obj),(UC_ARM_REG_R1,source),(UC_ARM_REG_R2,24),(UC_ARM_REG_R3,42),(UC_ARM_REG_LR,BASE)]:c.reg_write(reg,val)
 c.emu_start(0x88d184,BASE,count=300)
 assert c.reg_read(UC_ARM_REG_PC)==BASE
 ret=c.reg_read(UC_ARM_REG_R0);seq=struct.unpack('<I',c.mem_read(mapping+8,4))[0];out=bytes(c.mem_read(mapping+12,32));ok=label=='free'
 assert ret==(36 if ok else 0);assert seq==(42 if ok else state);assert out==(payload+b'\xa5'*8 if ok else b'\xa5'*32)
 results.append(dict(case=label,return_bytes=ret,sequence=seq,payload_exact=ok,calls=calls))
print(json.dumps(dict(binary_sha256=NAV,native_entry='0x88d184',cases=results,imports_modeled=['pthread_mutex_trylock','pthread_mutex_unlock','memcpy','failure diagnostics'],limitation='Native branch/copy arguments verified; actual QNX synchronization and consumer rearm not executed; no receiver or vehicle.'),indent=2))
