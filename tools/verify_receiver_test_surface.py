#!/usr/bin/env python3
from pathlib import Path
import struct,json,hashlib
from unicorn import *
from unicorn.arm_const import *
import argparse
parser=argparse.ArgumentParser(description='Offline execution of receiver test-surface selection, record copy and withdrawal; no vehicle connection.')
parser.add_argument('--image',type=Path,required=True)
parser.add_argument('--data',type=Path,required=True)
parser.add_argument('--scene',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
b=args.image.read_bytes();d=args.data.read_bytes()
for content,expected in [(b,'50130235f52573cc9facda89795486387ac4eb73a999026983694fd91d379761'),(d,'b33107cd3bc2b8133bea9b5636add414ce1a45aa6a43bc8b380a830fd7d92a58'),(args.scene.read_bytes(),'1d3fc97687f40571348761cd5ea33d41875aa11177456522693d786c8e1eda72')]:
 if hashlib.sha256(content).hexdigest()!=expected:raise SystemExit('Input SHA256 mismatch')
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x10000,(len(b)+4095)&~4095);u.mem_write(0x10000,b);u.mem_map(0xc50000,0x2380000);u.mem_write(0xc50000,d);u.mem_map(0x3000000,0x10000)
STOP=0x300fff0;OBJ=0x3001000;PAY=0x3002000;N1=0x3003000;N2=0x3004000
u.reg_write(UC_ARM_REG_SP,0x300f000)
u.emu_start(0x296efc|1,0x296f78,count=1000)
rows=[]
for v in range(256):
 u.reg_write(UC_ARM_REG_R0,v);u.reg_write(UC_ARM_REG_LR,STOP|1);u.emu_start(0x296edc|1,STOP,count=1000);assert u.reg_read(UC_ARM_REG_PC)==STOP
 ptr=u.reg_read(UC_ARM_REG_R0)
 if ptr:
  pos=ptr-65536;rows.append({'selector':v,'asset':b[pos:b.index(b'\0',pos)].decode()})
assert len(rows)==25
payload=bytes([0,17,34,51,1]);u.mem_write(PAY,payload);u.reg_write(UC_ARM_REG_R0,OBJ);u.reg_write(UC_ARM_REG_R1,PAY);u.reg_write(UC_ARM_REG_LR,STOP|1);u.emu_start(0x296bce|1,STOP,count=100)
assert bytes(u.mem_read(OBJ+0x18,6))==payload+b'\1'
u.mem_write(OBJ+0x28,struct.pack('<II',N1,N2));u.mem_write(N1+0x36,b'\1');u.mem_write(N2+0x36,b'\1');u.mem_write(OBJ+0x1c,b'\2');u.reg_write(UC_ARM_REG_R5,OBJ);u.emu_start(0x296c12|1,0x296ece,count=100)
assert u.reg_read(UC_ARM_REG_PC)==0x296ece
assert u.mem_read(N1+0x36,1)==b'\0' and u.mem_read(N2+0x36,1)==b'\0'
scene=args.scene.read_bytes()
bounds={hex(o):list(struct.unpack_from('<ff',scene,o+0x30)) for o in [0x658,0x6f0]}
assert all(v==[408.,132.] for v in bounds.values())
result={'image_sha256':hashlib.sha256(b).hexdigest(),'data_sha256':hashlib.sha256(d).hexdigest(),'bounds':bounds,'control_record':{'bytes':['selector','red','green','blue','enable'],'copied':list(u.mem_read(OBJ+0x18,6))},'asset_selectors':rows,'disabled_node_flags':[0,0],'native_blocks':['296efc..296f78','296edc','296bce','296c12(enable=2)..296ece'],'intercepts':0,'limits':'Older 004 firmware; asset selector lookup, record copy and actual enable=2 branch to disable executed. Full rendering and transport not executed. No arbitrary bitmap upload binding established.'}
args.output.write_text(json.dumps(result,indent=2)+'\n');print('256 selector cases, record copy and withdrawal passed; saved',args.output)
