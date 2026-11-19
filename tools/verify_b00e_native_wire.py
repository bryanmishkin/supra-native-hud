#!/usr/bin/env python3
"""Native ARM proof against the hash-pinned captured HMI; private inputs only."""
import sys,struct,json,hashlib
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Execute captured HMI native code offline; never contacts a vehicle.')
parser.add_argument('--hmi',type=Path,required=True)
parser.add_argument('--request',type=Path,required=True)
parser.add_argument('--tools-dir',type=Path,default=Path(__file__).resolve().parent)
args=parser.parse_args()
sys.path.insert(0,str(args.tools_dir))
from verify_pip_binding_records import *
p=args.hmi;sha='fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935'
results=[]
live=args.request.read_bytes()
if len(live)<46 or live[:4]!=bytes.fromhex("b00e0003") or int.from_bytes(live[4:8],"big")!=len(live)-8 or live[12:16]!=bytes([1,1,0,0]):
 raise ValueError("Expected captured B00E setResource request")
from ric_resource import decode_resource_body
parsed=decode_resource_body(live[16:])
if parsed.get("bitmap",{}).get("resolution_pair")!=[36,36] or parsed["bitmap"]["image_bytes"]>8192 or not parsed["bitmap"]["outer_identity_matches"]:
 raise ValueError("Expected bounded 36x36 bitmap fixture")
liveid,typ,lw,lh,ln=struct.unpack('>IBHHI',live[33:46])
assert ln==len(live[46:])
for w,h,data,identity in [(1,1,b'\xff\x00\x10\x20',0x01000001),(320,320,bytes(range(256)),0x01000001),(96,32,b'\x00'*64,0x01000001),(lw,lh,live[46:],liveid)]:
 c=cpu_for(p,sha);obj=BASE+0x1000;stream=BASE+0x2000;buf=BASE+0x8000;dims=BASE+0x3000;pixels=BASE+0x4000
 c.mem_write(obj,struct.pack('<IIIIIIII',identity,1,dims,dims+4,dims+4,pixels,pixels+len(data),pixels+len(data)))
 c.mem_write(dims,struct.pack('<HH',w,h));c.mem_write(pixels,data);c.mem_write(stream,struct.pack('<II',buf,buf))
 calls=[]
 def hook(uc,a,size,u):
  if a==0x299bb40:
   dst=uc.reg_read(UC_ARM_REG_R0);uc.mem_write(dst,struct.pack('<II',uc.reg_read(UC_ARM_REG_R1),uc.reg_read(UC_ARM_REG_R2)));uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));calls.append('stream-snapshot')
  elif a==0x299b360:
   st,src,n=[uc.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]];cur=struct.unpack('<I',uc.mem_read(st+4,4))[0]
   uc.mem_write(cur,bytes(uc.mem_read(src,n)));word(uc,st+4,cur+n);uc.reg_write(UC_ARM_REG_R0,n);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));calls.append('stream-write')
 c.hook_add(UC_HOOK_CODE,hook);c.reg_write(UC_ARM_REG_R0,obj);c.reg_write(UC_ARM_REG_R1,stream);c.reg_write(UC_ARM_REG_LR,BASE)
 try:c.emu_start(0x289ee58,BASE,count=200000)
 except Exception as e:print(hex(c.reg_read(UC_ARM_REG_PC)),e);raise
 end=struct.unpack('<I',c.mem_read(stream+4,4))[0];got=bytes(c.mem_read(buf,end-buf));want=struct.pack('>IBHHI',identity,1,w,h,len(data))+data
 assert got==want,(got.hex(),want.hex())
 if identity==liveid:assert got==live[33:]
 results.append({'width':w,'height':h,'data_length':len(data),'wire_hex':got.hex(),'match':True,'callback_counts':{k:calls.count(k) for k in set(calls)}})
print(json.dumps({'sha256':sha,'function':'0x289ee58','cases':results,'limitation':'Native serializer executed; only stream snapshot/write ABI callbacks emulated. No receiver decoding or rendering proven.'},indent=2))
