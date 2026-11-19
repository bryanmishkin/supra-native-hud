#!/usr/bin/env python3
"""Execute captured ARM publication gates; never contacts a car or simulates a receiver."""
import argparse,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--controller',type=Path,required=True);p.add_argument('--tools-dir',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();sys.path.insert(0,str(a.tools_dir))
from verify_pip_binding_records import *
results=[]
for connected,has_changes in [(False,False),(False,True),(True,False),(True,True)]:
 c=cpu_for(a.controller,CTL);sender=BASE+0x1000;changes=BASE+0x2000;vtable=BASE+0x3000;dispatch=BASE+0x4000;entries=BASE+0x5000
 word(c,sender,vtable);word(c,vtable+0x60,dispatch);c.mem_write(sender+0xf8,bytes([connected]));word(c,sender+0x15c,0)
 if has_changes:word(c,changes+0x1cc+4,entries);word(c,changes+0x1cc+8,entries+4);word(c,entries,0x02000004)
 c.reg_write(UC_ARM_REG_R0,sender);c.reg_write(UC_ARM_REG_R1,changes);events=[]
 def stop(cpu,addr,size,user):
  if addr in [dispatch,0x2dbf24]:
   events.append({'kind':'dedicated_pip_virtual_dispatch' if addr==dispatch else 'event_release','target':hex(addr),'r0':hex(cpu.reg_read(UC_ARM_REG_R0))});cpu.emu_stop()
 c.hook_add(UC_HOOK_CODE,stop);c.emu_start(0xa8b588,BASE,count=400)
 expected='dedicated_pip_virtual_dispatch' if connected and has_changes else 'event_release'
 assert len(events)==1 and events[0]['kind']==expected,(connected,has_changes,events)
 results.append({'connected':connected,'dedicated_changes_nonempty':has_changes,'destination_selector':0,'result':events[0]['kind']})
print(json.dumps({'sha256':CTL,'entry':'0xa8b588','native_vector_empty_helper':'0xa8a21c','cases':results,'external_functions_executed':0,'interception':'Stops before downstream virtual dispatch or event release. No called function is replaced.','limitation':'Proves publication gate predicates, not live object values, actual PiP upload, ownership, transport, or receiver rendering.'},indent=2))
