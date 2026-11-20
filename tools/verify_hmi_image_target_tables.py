import sys,json,struct,argparse
from pathlib import Path
from verify_pip_binding_records import cpu_for,BASE
from unicorn.arm_const import *
HMI='fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935'
parser=argparse.ArgumentParser(description='Execute captured HU image-target enum table setup offline.')
parser.add_argument('hmi',type=Path)
args=parser.parse_args()
results=[]
for name,start,stop,expected in [('imageTarget',0x25b8e10,0x25b8e5c,['NONE','HMI_ROADBOOK_SPLITSCREEN','HMI_ROADBOOK_PAD','HMI_GUIDING_LABELS_MAP']),('imageContentType',0x2602780,0x26027cc,['DEFAULT','INTERSECTION_VIEW','BRANCH_VIEW','BRANCH_REALISTIC_VIEW'])]:
 c=cpu_for(args.hmi,HMI)
 fp=BASE+0x2000;c.reg_write(UC_ARM_REG_FP,fp);c.reg_write(UC_ARM_REG_R4,BASE+0x1000);c.mem_write(fp-0x3c,bytes(32))
 c.emu_start(start,stop,count=64)
 rows=[]
 for i in range(4):
  value,pointer=struct.unpack('<II',c.mem_read(fp-0x3c+i*8,8));text=bytes(c.mem_read(pointer,80)).split(b'\0')[0].decode();assert value==i and text==expected[i];rows.append(dict(value=value,name=text))
 results.append(dict(field=name,entry=hex(start),stop=hex(stop),table=rows))
print(json.dumps(dict(sha256=HMI,intercepts=0,results=results,scope='Actual HU Roadbook enum table construction; not receiver routing.'),indent=2))
