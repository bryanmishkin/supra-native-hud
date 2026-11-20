"""Execute actual PiPNavi visibility arbitration, with synthetic scene trees."""
from pathlib import Path
import struct,json,hashlib,argparse
from unicorn import *
from unicorn.arm_const import *
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--image',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
raw=args.image.read_bytes()
if hashlib.sha256(raw).hexdigest()!='50130235f52573cc9facda89795486387ac4eb73a999026983694fd91d379761':
 raise SystemExit('Wrong receiver image: refusing version-specific offsets')

results=[]
for label,visible,parent_visible,old_visible,expect in [('visible',1,1,None,True),('hidden-self',0,1,None,False),('hidden-parent',1,0,None,False),('visible-old-owner',1,1,1,False),('hidden-old-owner',1,1,0,True)]:
 u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x10000,(len(raw)+4095)&~4095);u.mem_write(0x10000,raw);u.mem_map(0x2300000,0x200000);u.mem_map(0x3000000,0x10000)
 widget,node,parent,old,oldnode=0x3001000,0x3002000,0x3003000,0x3004000,0x3005000;stop=0x300e000
 def w(a,v):u.mem_write(a,struct.pack('<I',v))
 w(widget+12,node);u.mem_write(node+0xb8,bytes([visible]));w(node+0xe4,parent);u.mem_write(parent+0xb8,bytes([parent_visible]));w(parent+0xe4,0)
 if old_visible is not None:w(0x23944b4,old);w(old+12,oldnode);u.mem_write(oldnode+0xb8,bytes([old_visible]));w(oldnode+0xe4,0)
 calls=[];targets={0x2d80de:'old-owner-release',0x2d7e6c:'old-images-hide',0x2d7e30:'new-images-show',0x2d809c:'new-owner-refresh',0x2d7d86:'widget-update'}
 def hook(u,a,s,d):
  if a in targets:
   calls.append({'function':targets[a],'object':hex(u.reg_read(UC_ARM_REG_R0))});u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
 u.hook_add(UC_HOOK_CODE,hook);u.reg_write(UC_ARM_REG_SP,0x300f000);u.reg_write(UC_ARM_REG_R0,widget);u.reg_write(UC_ARM_REG_LR,stop|1);u.emu_start(0x28e577,stop,count=1000)
 owner=struct.unpack('<I',u.mem_read(0x23944b4,4))[0];accepted=any(x['function']=='widget-update' for x in calls);assert accepted==expect,(label,calls)
 results.append(dict(case=label,accepted=accepted,owner=hex(owner),intercepted_calls=calls))
args.output.write_text(json.dumps({'scope':'older004 firmware; synthetic trees; actual arbitration branches, downstream render calls intercepted','cases':results},indent=2));print(json.dumps(results))
