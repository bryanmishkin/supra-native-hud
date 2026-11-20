#!/usr/bin/env python3
from pathlib import Path
import struct,json
from unicorn import *
from unicorn.arm_const import *
import argparse,hashlib
parser=argparse.ArgumentParser(description='Offline receiver internal test-surface input replay. No vehicle or external transport.')
parser.add_argument('--image',type=Path,required=True)
parser.add_argument('--data',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();b=args.image.read_bytes();d=args.data.read_bytes()
for content,expected in [(b,'50130235f52573cc9facda89795486387ac4eb73a999026983694fd91d379761'),(d,'b33107cd3bc2b8133bea9b5636add414ce1a45aa6a43bc8b380a830fd7d92a58')]:
 if hashlib.sha256(content).hexdigest()!=expected:raise SystemExit('Input SHA256 mismatch')
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x10000,(len(b)+4095)&~4095);u.mem_write(0x10000,b);u.mem_map(0xc50000,0x2380000);u.mem_write(0xc50000,d);u.mem_map(0x3000000,0x10000)
u.mem_write(0xc6faa0,b'\1');u.mem_write(0xd4cc94,struct.pack('<I',2));u.mem_write(0x1142631,b'\1');u.mem_write(0x3001000,bytes([0,17,34,51,1,1]));u.reg_write(UC_ARM_REG_SP,0x300f000);u.reg_write(UC_ARM_REG_R0,0x16e);u.reg_write(UC_ARM_REG_R1,0x3001000);u.reg_write(UC_ARM_REG_R2,6);u.reg_write(UC_ARM_REG_LR,0x300fff1)
seen=[]
def hook(u,a,size,user):
 if a in [0x14267c,0x140e5c,0x142314,0x149f30,0x15bd00,0x142744,0x3fc40a,0x190cd2]:seen.append({'pc':hex(a),'r0':hex(u.reg_read(UC_ARM_REG_R0)),'r1':hex(u.reg_read(UC_ARM_REG_R1))})
 if a==0x190cd2:
  arg=u.reg_read(UC_ARM_REG_R0);event=u.reg_read(UC_ARM_REG_R1);seen.append({'event':hex(event),'payload':list(u.mem_read(arg,5))});u.emu_stop()
u.hook_add(UC_HOOK_CODE,hook)
u.emu_start(0x14267d,0x300fff0,count=200000)
assert u.reg_read(UC_ARM_REG_PC)==0x190cd2
assert seen[-1]=={'event':'0xac','payload':[0,17,34,51,1]}
print('Native internal receive-to-widget-event route passed; saved',args.output)
args.output.write_text(json.dumps({'trace':seen,'final_pc':hex(u.reg_read(UC_ARM_REG_PC)),'scope':'Synthetic receive record; stops at event enqueue; not a transport or rendering test','intercepts':0},indent=2)+'\n')
assert seen[-1]=={'event':'0xac','payload':[0,17,34,51,1]}
