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
from ric_rle32 import decode_bgra,encode_bgra
p=args.hmi;sha='fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935'
live=args.request.read_bytes()
if len(live)<46 or live[:4]!=bytes.fromhex("b00e0003") or int.from_bytes(live[4:8],"big")!=len(live)-8 or live[12:16]!=bytes([1,1,0,0]):
 raise ValueError("Expected captured B00E setResource request")
from ric_resource import decode_resource_body
parsed=decode_resource_body(live[16:])
if parsed.get("bitmap",{}).get("resolution_pair")!=[36,36] or parsed["bitmap"]["image_bytes"]>8192 or not parsed["bitmap"]["outer_identity_matches"]:
 raise ValueError("Expected bounded 36x36 bitmap fixture")
cases=[('live-ruler',live[46:],36*36)]
for n in [1,127,128,255]:
 raw=b'\x12\x34\x56\xff'*n+bytes([3,2,1,255])*3;cases.append(('mixed-'+str(n),encode_bgra(raw),len(raw)//4))
for count in [127,128,255]:
 raw=b"".join(bytes([i%256,(i*3)%256,(i*7)%256,255]) for i in range(count))
 cases.append(("literal-"+str(count),encode_bgra(raw),count))
results=[]
for name,data,n in cases:
 c=cpu_for(p,sha);fp=BASE+0xf000;obj=BASE+0x1000;inp=BASE+0x2000;out=BASE+0x6000
 word(c,obj,inp);c.mem_write(inp,data);word(c,fp-0x110,obj);word(c,fp-0x108,len(data));word(c,fp-0x10c,n*4+18);word(c,fp-0x84,out)
 c.reg_write(UC_ARM_REG_FP,fp);c.reg_write(UC_ARM_REG_R2,0);c.reg_write(UC_ARM_REG_R3,18)
 def guard(uc,a,size,u):
  if a in [0x2625734,0x2625838]:raise RuntimeError('native decoder out of bounds')
 c.hook_add(UC_HOOK_CODE,guard);c.emu_start(0x2625924,0x2625954,count=200000)
 assert c.reg_read(UC_ARM_REG_PC)==0x2625954
 got=bytes(c.mem_read(out+18,n*4));bgra=decode_bgra(data,n);rgba=b''.join(bytes([bgra[i+2],bgra[i+1],bgra[i],bgra[i+3]]) for i in range(0,len(bgra),4))
 assert got==rgba
 results.append({'case':name,'pixels':n,'encoded_bytes':len(data),'native_output_sha256':hashlib.sha256(got).hexdigest(),'matches_rgba':True,'consumed_bytes':c.reg_read(UC_ARM_REG_R2),'produced_bytes':c.reg_read(UC_ARM_REG_R3)-18})
print(json.dumps({'binary_sha256':sha,'native_loop':'0x26256f0–0x2625930','cases':results,'external_callbacks':'none; complete loop uses only memory operations','limitation':'Head-unit Roadbook RIC adaptor decoder; not cluster receiver execution or widget binding proof.'},indent=2))
