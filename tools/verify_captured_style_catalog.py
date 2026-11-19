#!/usr/bin/env python3
"""Check actual captured XPD view lookups against hash-pinned ARM code offline."""
import argparse,json,hashlib
from pathlib import Path
from catalog_guidance_styles import catalog
from style_xpd import Xpd,guiding_view_keys,xar_entries
from verify_pip_binding_records import cpu_for,word,BASE,NAV
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_LR,UC_ARM_REG_PC

def verify(nav,capture):
 manifest=json.loads((capture/'manifest.json').read_text());expected=catalog(capture)['views'];results=[]
 for remote,row in manifest['files'].items():
  views=[v for v in expected if v['file']==Path(remote).name and 'node_offset' in v]
  if not views:continue
  data=(capture/row['file']).read_bytes()
  if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Capture hash mismatch')
  cpu=cpu_for(nav,NAV);blob=0x31000000;cpu.mem_map(blob,(len(data)+4095)&~4095);cpu.mem_write(blob,data)
  xpd=next(x for x in xar_entries(data) if x['kind']=='XPD');db=BASE+0x1000;keys=BASE+0x2000;word(cpu,db+4,blob+xpd['offset']+4)
  for view in views:
   k=guiding_view_keys(view['view'])
   for i,value in enumerate(k):word(cpu,keys+4*i,value)
   for reg,value in [(UC_ARM_REG_R0,db),(UC_ARM_REG_R1,blob+xpd['offset']+4),(UC_ARM_REG_R2,keys),(UC_ARM_REG_R3,len(k)),(UC_ARM_REG_LR,BASE+0xf100)]:cpu.reg_write(reg,value)
   cpu.emu_start(0x6366d0,BASE+0xf100,count=200000)
   if cpu.reg_read(UC_ARM_REG_PC)!=BASE+0xf100:raise ValueError('Native lookup did not return')
   found=cpu.reg_read(UC_ARM_REG_R0)-blob
   if found!=view['node_offset']:raise ValueError('Native/Python node disagreement')
   results.append({'file':view['file'],'view':view['view'],'node_offset':found,'matched':True})
 return {'binary_sha256':NAV,'native_function':'0x6366d0','callbacks_intercepted':0,'cases':results,'all_matched':True,'vehicle_contact':False,'limit':'Actual lookup verified; no graphics driver or physical receiver is emulated.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--nav',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=verify(a.nav,a.capture);a.output.write_text(json.dumps(r,indent=2)+'\n');print(len(r['cases']),'actual style lookups match native ARM')
