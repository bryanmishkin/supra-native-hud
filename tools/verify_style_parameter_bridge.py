#!/usr/bin/env python3
"""Execute captured manifest-parameter copy and consumer accessor offline."""
import argparse,hashlib,json,struct
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--basic',type=Path,required=True);p.add_argument('--fully',type=Path,required=True);a=p.parse_args()
BASIC_SHA='d03464928749857ceab8daec20db422cf81d47f722ae4bb9d9c54a03057c1206'
rows=[]
for name,values in [('StandardGVDay',[3,0,0,48]),('StandardGVNight',[3,1,0,48])]:
 c=cpu_for(a.basic,BASIC_SHA);src=BASE+0x1000;rec=BASE+0x2000
 c.mem_write(src,struct.pack('<4I',*values));word(c,BASE+0xf000+0x110,src);c.reg_write(UC_ARM_REG_R0,rec)
 c.emu_start(0x5b6358,0x5b638c,count=64)
 params=bytes(c.mem_read(rec+4,16))
 assert params[:13]==struct.pack('<3IB',*values)
 c=cpu_for(a.fully,NAV);src=BASE+0x1000;obj=BASE+0x2000
 c.mem_write(src,params);c.reg_write(UC_ARM_REG_R0,obj);c.reg_write(UC_ARM_REG_R1,src);c.reg_write(UC_ARM_REG_LR,BASE+0xf100)
 c.emu_start(0x88e96c,BASE+0xf100,count=64)
 scalar=int.from_bytes(c.mem_read(obj+0x10,4),'little');assert scalar==values[1]
 rows.append({'style':name,'manifest_values':values,'catalog_params_hex':params[:13].hex(),'accessor_plus_0x10':scalar,'style_flag':scalar==0})
print(json.dumps({'basic_sha256':BASIC_SHA,'fully_sha256':NAV,'cases':rows,'executed_ranges':['5b6358..5b6388','88e96c..88e97c'],'intercepts':[],'limitation':'Executes exact parameter copy and accessor storage; lookup/serialization chain separately statically traced. Does not prove which style is selected live.'},indent=2))
