#!/usr/bin/env python3
"""Execute native view-set post-render picture-counter updates, offline."""
import argparse,json
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--nav',type=Path,required=True);a=p.parse_args();rows=[]
for paired in [False,True]:
 c=cpu_for(a.nav,NAV);obj=BASE+0x1000;array=BASE+0x2000;v1=BASE+0x3000;v2=BASE+0x4000
 word(c,obj,0xa0dac0);word(c,obj+12,array);word(c,array,v1);word(c,array+4,v2 if paired else 0)
 for v,n in [(v1,17),(v2,29)]:word(c,v,0xa0e140);word(c,v+0xa8,n)
 c.reg_write(UC_ARM_REG_R0,obj);c.reg_write(UC_ARM_REG_LR,BASE+0xf100);c.emu_start(0x61b170,BASE+0xf100,count=256)
 got=[int.from_bytes(c.mem_read(v+0xa8,4),'little') for v in [v1,v2]];assert got==[18,30 if paired else 29]
 rows.append({'paired':paired,'initial':[17,29],'after':got})
print(json.dumps({'sha256':NAV,'entry':'0x61b170','viewset_vtable':'0xa0dac0','view_vtable':'0xa0e140','cases':rows,'intercepts':[],'limitation':'Counter forwarding executes unchanged. Manager branch ordering is statically traced; no receiver or physical frame cadence is simulated.'},indent=2))
