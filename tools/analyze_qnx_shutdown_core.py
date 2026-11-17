#!/usr/bin/env python3
"""Offline QNX 6.5 ARM core-note summary. No target execution.
Status layout is the 224-byte QNX debug_thread_t from the SDK. Symbol labels
require an independently supplied libc load base and matching captured libc.
"""
import argparse,json,struct,hashlib
from pathlib import Path
from elftools.elf.elffile import ELFFile
def status_note(data):
 if len(data)!=224:raise ValueError('Unknown QNX status-note layout')
 pid,tid=struct.unpack_from('<II',data);signo,code,err,flt,ip,addr=struct.unpack_from('<iiiIII',data,88)
 return {'pid':pid,'tid':tid,'signal':signo,'signal_code':code,'fault_ip':hex(ip),'fault_address':hex(addr)}
def analyze(core,libc,base):
 threads=[];process=None;current=None
 with core.open('rb') as f:
  e=ELFFile(f)
  if e.elfclass!=32 or e['e_machine']!='EM_ARM' or not e.little_endian or e['e_type']!='ET_CORE':raise ValueError('Expected ARM little-endian ELF32 core')
  for seg in e.iter_segments():
   if seg['p_type']!='PT_NOTE':continue
   for n in seg.iter_notes():
    if n['n_name']!='QNX':continue
    data=n['n_desc'];kind=n['n_type']
    if kind==7:
     if len(data)!=272:raise ValueError('Unknown QNX process-note layout')
     process=struct.unpack_from('<I',data)[0]
    if kind==8:
     current=status_note(data);threads.append(current)
    if kind==9 and current is not None:
     if len(data)!=68:raise ValueError('Unknown ARM register note')
     regs=struct.unpack('<17I',data);current.update(pc=hex(regs[15]),lr=hex(regs[14]),sp=hex(regs[13]))
 with libc.open('rb') as f:
  e=ELFFile(f);dyn=next(s for s in e.iter_segments() if s['p_type']=='PT_DYNAMIC');symbols=sorted([(s['st_value'],s['st_size'],s.name) for s in dyn.iter_symbols() if s['st_value'] and s['st_size']])
 for t in threads:
  for key in ['pc','lr','fault_ip']:
   if key not in t:continue
   offset=int(t[key],16)-base;matches=[s for s in symbols if s[0]<=offset<s[0]+s[1]]
   if matches:
    v,size,name=matches[-1];t[key+'_libc_symbol']={'name':name,'offset':offset-v}
 return {'core_sha256':hashlib.sha256(core.read_bytes()).hexdigest(),'process_pid':process,'libc_sha256':hashlib.sha256(libc.read_bytes()).hexdigest(),'supplied_libc_load_base':hex(base),'symbolization_limit':'Symbol labels depend on supplied base/library match; PID and signal come directly from core notes. Core alone does not prove the system reset policy.','threads':threads}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('core',type=Path);p.add_argument('--libc',type=Path,required=True);p.add_argument('--libc-base',type=lambda s:int(s,0),required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.core,a.libc,a.libc_base);a.output.write_text(json.dumps(r,indent=2));print(json.dumps({'pid':r['process_pid'],'threads':len(r['threads'])}))
