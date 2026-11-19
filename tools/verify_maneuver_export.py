"""Execute the captured generated ManeuverView export constructor, offline only."""
import argparse,json
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--nav',required=True,type=Path);a=p.parse_args()
c=cpu_for(a.nav,NAV);out=BASE+0x1000;stack=BASE+0xf000
for reg,value in [(UC_ARM_REG_R0,out),(UC_ARM_REG_R1,0x9445ad),(UC_ARM_REG_R2,15),(UC_ARM_REG_R3,1),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,BASE+0xf100)]:c.reg_write(reg,value)
for off,value in [(0,32),(4,0),(8,0x1bd170),(12,0x1bd138)]:word(c,stack+off,value)
c.emu_start(0x108780,BASE+0xf100,count=500)
raw=bytes(c.mem_read(out,32));assert int.from_bytes(raw[0:4],'little')==0x9445ad
assert int.from_bytes(raw[12:14],'little')==32 and int.from_bytes(raw[14:16],'little')==0
assert int.from_bytes(raw[24:28],'little')==0x9445ad
print(json.dumps({'sha256':NAV,'constructor':'0x108780','initializer':'0x10d80c..0x10d834','role':'ManeuverView.DNAVIManeuverView','major':32,'minor':0,'record_hex':raw.hex(),'intercepts':[],'limitation':'Actual generated constructor execution with arguments established statically; no broker connection or export acceptance is claimed.'},indent=2))
