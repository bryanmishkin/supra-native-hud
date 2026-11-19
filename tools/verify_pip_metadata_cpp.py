#!/usr/bin/env python3
"""Compare a host-built C++ producer codec with executed native ARM records."""
import argparse,json,subprocess,tempfile
from pathlib import Path
from verify_pip_metadata_record import verify
from pip_metadata_strip import encode_record
from pip_metadata_record import build_bgra_framebuffer

def check(nav):
 evidence=verify(nav)
 root=Path(__file__).resolve().parents[1]
 code=['#include <stdio.h>','#include "native_metadata_record.hpp"','int main() { unsigned char p[84];']
 expected=[]
 for row in evidence['cases']:
  args=f"{row['guidance_type']}u,0x1234u,0x0f000004u,{row['option_zero']}u,{int(row['style_flag'])}"
  for fn in ['native_metadata_record','native_metadata_rgba_upload','native_metadata_bgra_framebuffer']:
   code.append('{ supra_pip::MetadataInput x={'+args+'};')
   code.append('if (!supra_pip::'+fn+'(p,84,x)) return 1;')
   code.append('for(unsigned i=0;i<84;++i) printf("%02x",p[i]); puts(""); }')
   raw=bytes.fromhex(row['record_hex'])
   if fn=='native_metadata_bgra_framebuffer':
    result=build_bgra_framebuffer(row['guidance_type'],0x1234,0x0f000004,row['style_flag'],row['option_zero'])
   else:result=raw if fn=='native_metadata_record' else encode_record(raw)
   expected.append(result.hex())
 code.append('return 0; }')
 with tempfile.TemporaryDirectory(prefix='supra-metadata-') as t:
  p=Path(t);(p/'check.cpp').write_text('\n'.join(code))
  subprocess.run(['c++','-std=c++98','-Wall','-Wextra','-Werror','-I',str(root/'tools/pip/include'),str(p/'check.cpp'),'-o',str(p/'check')],check=True,capture_output=True)
  got=subprocess.run([str(p/'check')],check=True,capture_output=True,text=True).stdout.splitlines()
  assert got==expected
 return dict(binary_sha256=evidence['binary_sha256'],native_records=len(evidence['cases']),cpp_outputs=len(got),all_match=True,vehicle_contact=False,receiver_binding_proven=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('nav',type=Path);a=p.parse_args();print(json.dumps(check(a.nav),indent=2))
