#!/usr/bin/env python3
"""Execute the older receiver state engine offline; never contacts a vehicle."""
from pathlib import Path
import argparse
import struct,json,hashlib
from unicorn import *
from unicorn.arm_const import *
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--image',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
b=args.image.read_bytes()
if hashlib.sha256(b).hexdigest()!='50130235f52573cc9facda89795486387ac4eb73a999026983694fd91d379761':
 raise SystemExit('Receiver image SHA256 mismatch')
BASE=0x6231a4;ENGINE=0xd00670;STOP=0x300fff0;OUT=0x3001000
def symbol_names(count,table,pool,fmt):
 result={}
 for i in range(count):
  rel=struct.unpack_from('<'+fmt,b,BASE-65536+table+i*struct.calcsize(fmt))[0]
  pos=BASE-65536+pool+rel
  result[i]=b[pos:b.index(b'\0',pos)].decode('utf-8')
 return result
state_names=symbol_names(0xa88,0x5ca8c,0x3c970,'I')
actions_names=symbol_names(0x1a0,0x61c4e,0x5f4ac,'H')
def reg(state):return struct.unpack_from('<H',b,BASE-65536+state*2)[0]
rows=[]
for link in [0x6ec,0x6ed]:
 for event,ready in [(0xc5,True),(0xc6,False),(0xc7,True)]:
  u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x10000,(len(b)+4095)&~4095);u.mem_write(0x10000,b);u.mem_map(0xc50000,0x2380000);u.mem_map(0x3000000,0x10000)
  u.mem_write(ENGINE+0x10,b'\xff'*(0x47f*2));u.mem_write(ENGINE+0x90e,b'\xff'*(0x47f*2));u.mem_write(ENGINE+1,b'\1')
  seeds=[0x6df,link,0x6eb,0x6f if ready else 0x6e,0x69 if ready else 0x68,0x6e7,0x72,0x74]
  for s in seeds:u.mem_write(ENGINE+0x10+reg(s)*2,struct.pack('<H',s))
  def call(entry,arg):
   u.reg_write(UC_ARM_REG_SP,0x300f000);u.reg_write(UC_ARM_REG_LR,STOP|1);u.reg_write(UC_ARM_REG_R0,arg);u.emu_start(entry|1,STOP,count=2000000)
   assert u.reg_read(UC_ARM_REG_PC)==STOP,hex(u.reg_read(UC_ARM_REG_PC))
   return u.reg_read(UC_ARM_REG_R0)
  assert call(0x2a7676,event)==0
  actions=[]
  for i in range(100):
   result=call(0x2a7696,OUT)
   if result==0:break
   assert result==1,result
   actions.append(struct.unpack('<H',u.mem_read(OUT,2))[0])
  else:raise AssertionError('action bound exceeded')
  assert call(0x2a78dc,0)==0
  expected=([0x37] if event!=0xc6 else [0x38]) if link==0x6ec else ([0x35] if event!=0xc6 else [0x36])
  assert actions==expected,(hex(link),hex(event),actions,expected)
  states={state_names[s]:hex(struct.unpack('<H',u.mem_read(ENGINE+0x10+reg(s)*2,2))[0]) for s in [0x6e7,0x6e,0x68]}
  rows.append({'link':state_names[link],'event':hex(event),'seed_states':[state_names[s] for s in seeds],'actions':[{'id':hex(a),'name':actions_names[a]} for a in actions],'final_states':states,'intercepts':0,'scope':'Actual state engine and transition data; synthetic initial states; returned rendering actions are not executed'})
args.output.write_text(json.dumps({'image_sha256':hashlib.sha256(b).hexdigest(),'cases':rows},indent=2)+'\n')
print(f'{len(rows)} native guidance-policy cases passed; saved {args.output}')
