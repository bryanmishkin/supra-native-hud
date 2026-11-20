#!/usr/bin/env python3
"""Execute hash-pinned older Supra receiver code with explicitly intercepted boundaries.
OEM image is supplied privately by caller and is not included in this repository.
"""
from pathlib import Path
import argparse,json,hashlib,struct
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import *
parser=argparse.ArgumentParser(description="Offline native receiver sink verification; no vehicle connection.")
parser.add_argument("--image", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args=parser.parse_args()
p=args.image;b=p.read_bytes()
EXPECTED="50130235f52573cc9facda89795486387ac4eb73a999026983694fd91d379761"
if hashlib.sha256(b).hexdigest()!=EXPECTED:
 parser.error("Image hash differs from verified SWFL 00005ffc 004_000_003; offsets must not be reused")
BASE=0x10000;STACK=0x3000000;STOP=STACK+0xff00
results=[]
def cpu():
 u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(BASE,(len(b)+4095)&~4095);u.mem_write(BASE,b);u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000);u.mem_map(STACK,0x10000);u.reg_write(UC_ARM_REG_SP,STACK+0xf000);u.reg_write(UC_ARM_REG_LR,STOP|1);return u
for sel in [0,1]:
 u=cpu();u.reg_write(UC_ARM_REG_R1,sel);rec={}
 def hook(u,a,s,d):
  if a==BASE+0x14bf5a:
   vals=[u.reg_read(x) for x in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]]
   rec.update(aspect=struct.unpack('<d',u.mem_read(vals[0],8))[0],dimensions=list(struct.unpack('<HH',u.mem_read(vals[1],4))),selection=u.mem_read(vals[2],1)[0]);u.reg_write(UC_ARM_REG_R0,1);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
  if a==STOP:u.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start((BASE+0x197984)|1,STOP,count=1000);results.append({'case':'sendNewDisplaySink','input':sel,**rec})
for val in [0,1,2,255]:
 u=cpu();ptr=STACK+0x100;u.mem_write(ptr+4,bytes([val]));u.reg_write(UC_ARM_REG_R6,ptr)
 def stop(u,a,s,d):
  if a==BASE+0x2a72bc:u.emu_stop()
 u.hook_add(UC_HOOK_CODE,stop);u.emu_start((BASE+0x2a72a0)|1,BASE+0x2a72bc,count=100)
 results.append({'case':'metadata_sink_decode','metadata_byte4':val,'internal_sink':u.reg_read(UC_ARM_REG_R6)})
for sel in [0,1]:
 u=cpu(); app=STACK+0x100; sink=STACK+0x200
 u.mem_write(app,b'\0'*24);u.mem_write(app+4,struct.pack('<I',sink+4));u.mem_write(sink+4,struct.pack('<I',0x518f34));u.reg_write(UC_ARM_REG_R0,app);u.reg_write(UC_ARM_REG_R1,sel);rec={}
 def dispatch(u,a,size,d):
  if a==BASE+0x1978ea:
   rec.update(request_this=u.reg_read(UC_ARM_REG_R0),requested_selection=u.reg_read(UC_ARM_REG_R1));u.reg_write(UC_ARM_REG_R0,1);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
 u.hook_add(UC_HOOK_CODE,dispatch);u.emu_start((BASE+0x2a7742)|1,STOP,count=100)
 rec['expected_sink']=u.mem_read(app,1)[0]
 assert rec=={'request_this':sink,'requested_selection':sel,'expected_sink':sel+1}
 results.append({'case':'expected_sink_setter_and_real_vtable_thunk','input':sel,**rec})
for expected,metadata in [(1,0),(1,1),(2,0),(2,1)]:
 u=cpu();u.mem_map(0x2400000,0x200000);app=0x241a748
 u.mem_write(app,bytes([expected,1])+b'\0'*22);u.mem_write(app+8,b'\xff\xff'*5)
 slot=STACK+0x100;u.mem_write(slot,b'\0');u.reg_write(UC_ARM_REG_R0,0x119);u.reg_write(UC_ARM_REG_R1,slot)
 record=bytearray(150);record[0:2]=b'\0\x01';record[4]=metadata;events=[]
 def callback_hooks(u,a,size,d):
  if a==BASE+0x180cde:
   assert u.reg_read(UC_ARM_REG_R1)==0x11c
   u.mem_write(u.reg_read(UC_ARM_REG_R0),bytes(record));u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
  elif a==BASE+0x393a50:
   u.mem_write(u.reg_read(UC_ARM_REG_R0),b'\0'*u.reg_read(UC_ARM_REG_R1));u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
  elif a==BASE+0x2ccb66:
   u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
  elif a==BASE+0x180cd6:
   events.append(u.reg_read(UC_ARM_REG_R1));u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
 u.hook_add(UC_HOOK_CODE,callback_hooks);u.emu_start((BASE+0x2a6a9c)|1,STOP,count=5000)
 assert events==([0x2ae] if expected==metadata+1 else [])
 results.append({'case':'full_metadata_callback','expected_sink':expected,'metadata_byte4':metadata,'emitted_events':events})
assert [x['dimensions'] for x in results[:2]]==[[277,160],[460,237]]
assert [x['internal_sink'] for x in results[2:6]]==[1,2,0,0]
out={'sha256':hashlib.sha256(b).hexdigest(),'source':str(p),'process_base':hex(BASE),'qualification':'Older same family 004_000_003; Native sender boundary intercepted; full callback uses supplied local event bytes and stubs logging, memset, event delivery. No receiver hardware simulation','results':results}
args.output.write_text(json.dumps(out,indent=2));print(json.dumps(results,indent=2))
