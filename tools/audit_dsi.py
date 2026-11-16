#!/usr/bin/env python3
"""Inspect captured DSI exports without loading or executing a vehicle library."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from elftools.elf.elffile import ELFFile

def audit(library, adapter):
    required = sorted(set(re.findall(r'need\(lib_,\s*"([^"]+)"\)', adapter.read_text())))
    if len(required) != 10:
        raise ValueError('Adapter symbol contract changed; review expected requirements')
    with library.open('rb') as f:
        e=ELFFile(f);dyn=e.get_section_by_name('.dynsym')
        exports={s.name:s for s in dyn.iter_symbols() if s['st_shndx']!='SHN_UNDEF'} if dyn else {}
        missing=[n for n in required if n not in exports]
        table=exports.get('_ZTV10CDSIClient')
        size=table['st_size'] if table is not None else None
        shape=e.elfclass==32 and e.little_endian and e['e_machine']=='EM_ARM'
    return {'library':library.name,'sha256':hashlib.sha256(library.read_bytes()).hexdigest(),
            'arm32_little_endian':shape,'required_symbols':required,'missing_symbols':missing,
            'client_vtable_bytes':size,'static_contract_passed':shape and not missing and size==40,
            'limits':'Symbol presence and 8-slot table extent only. Not a complete constructor/subobject, thread-lifetime or on-car callback ABI validation.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('library',type=Path)
    p.add_argument('--adapter',type=Path,default=Path(__file__).parents[1]/'vendor/nbt/src/dsi_client.cpp')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.library,a.adapter);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return 0 if r['static_contract_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
