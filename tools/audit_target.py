#!/usr/bin/env python3
"""Static QNX candidate gate. Requires pyelftools. Never executes the candidate."""
import argparse,hashlib,json
from pathlib import Path
from elftools.elf.elffile import ELFFile

def inspect(path):
 with path.open('rb') as f:
  e=ELFFile(f);d=next((x for x in e.iter_segments() if x['p_type']=='PT_DYNAMIC'),None)
  sy=e.get_section_by_name('.dynsym') or d
  result={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bits':e.elfclass,'machine':e['e_machine'],'little_endian':e.little_endian,'type':e['e_type'],'needed':[],'soname':path.name,'exports':[],'imports':[],'interpreter':None}
  for segment in e.iter_segments():
   if segment['p_type']=='PT_INTERP':result['interpreter']=segment.get_interp_name()
  if d:
   for t in d.iter_tags():
    if t.entry.d_tag=='DT_NEEDED':result['needed'].append(t.needed)
    if t.entry.d_tag=='DT_SONAME':result['soname']=t.soname
  if sy:
   for s in sy.iter_symbols():
    if not s.name:continue
    if s['st_shndx']=='SHN_UNDEF':result['imports'].append({'name':s.name,'weak':s['st_info']['bind']=='STB_WEAK'})
    elif s['st_info']['bind'] in ('STB_GLOBAL','STB_WEAK') and s['st_other']['visibility'] in ('STV_DEFAULT','STV_PROTECTED'):result['exports'].append(s.name)
  return result

def audit(binary,runtime):
 candidate=inspect(binary);catalog={};checks=[]
 for path in runtime.glob('*.so*'):
  lib=inspect(path);catalog[path.name]=catalog[lib['soname']]=lib
 pending=list(candidate['needed']);seen=set();libraries=[];missing=[]
 while pending:
  name=pending.pop()
  if name in seen:continue
  seen.add(name)
  if name not in catalog:missing.append(name);continue
  lib=catalog[name];libraries.append(lib);pending.extend(lib['needed'])
 exported={n for r in libraries+[candidate] for n in r['exports']}
 unresolved=[s['name'] for s in candidate['imports'] if not s['weak'] and s['name'] not in exported]
 checks.append({'check':'ARM32 little endian','pass':candidate['bits']==32 and candidate['machine']=='EM_ARM' and candidate['little_endian']})
 checks.append({'check':'dynamic executable with interpreter','pass':candidate['type'] in ('ET_EXEC','ET_DYN') and bool(candidate['interpreter'])})
 checks.append({'check':'captured dependency names','pass':not missing})
 checks.append({'check':'strong imported symbol names','pass':not unresolved})
 return {'candidate':candidate,'checks':checks,'missing_libraries':missing,'unresolved_strong_symbols':unresolved,'static_gate_passed':all(c['pass'] for c in checks),'limits':'Not a deployment approval. Verify interpreter, symbol versions, ABI, ownership and live behavior separately.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary',type=Path);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=audit(a.binary,a.runtime);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'checks':r['checks'],'static_gate_passed':r['static_gate_passed']}));return 0 if r['static_gate_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
