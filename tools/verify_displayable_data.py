#!/usr/bin/env python3
"""Execute captured DisplayableData serializer and check offline decoder."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import *
from verify_guidance_payload_codec import native_text,STRING_SHA
from guidance_payload import decode_displayable_data

def verify(controller,strings):
    rows=[]
    for user_id,name,maneuver,guidance_type,count,sequence in [(17,'GVBitmap_17',42,8301,256000,1),(91,'own',0xfffffffe,8402,512,37)]:
        c=cpu_for(controller,CTL)
        stream,table,writer,obj,data=[BASE+i for i in (0x1000,0x2000,0x3000,0x4000,0x5000)]
        word(c,stream,table);word(c,table+0x18,writer)
        for i,v in enumerate((user_id,data,maneuver,guidance_type,count,sequence)):word(c,obj+i*4,v)
        raw=name.encode();word(c,data+8,len(raw));c.mem_write(data+0x11,raw+b'\0');chunks=[]
        def boundary(cpu,a,size,user):
            if a==writer:
                ptr,n=cpu.reg_read(UC_ARM_REG_R1),cpu.reg_read(UC_ARM_REG_R2)
                chunks.append(bytes(cpu.mem_read(ptr,n)));cpu.reg_write(UC_ARM_REG_R0,n)
                cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
            elif a==0x127400:
                chunks.append(native_text(strings,raw));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        c.hook_add(UC_HOOK_CODE,boundary)
        c.reg_write(UC_ARM_REG_R0,stream);c.reg_write(UC_ARM_REG_R1,obj);c.reg_write(UC_ARM_REG_LR,BASE)
        c.emu_start(0x1d3b88,BASE,count=300)
        assert c.reg_read(UC_ARM_REG_PC)==BASE
        wire=b''.join(chunks)
        expected=struct.pack('<II',user_id,len(raw))+raw+struct.pack('<IIII',maneuver,guidance_type,count,sequence)
        assert wire==expected
        decoded=decode_displayable_data(wire)
        assert tuple(decoded.values())==(user_id,name,maneuver,guidance_type,count,sequence)
        for invalid in (wire[:-1],wire+b'\0',wire[:4]+struct.pack('<I',4097)+wire[8:]):
            try:decode_displayable_data(invalid)
            except ValueError:pass
            else:raise AssertionError('Invalid metadata accepted')
        rows.append(dict(decoded=decoded,hex=wire.hex()))
    return dict(controller_sha256=CTL,string_library_sha256=STRING_SHA,cases=rows,
      event='0x80000004',serializer='0x1d3b88',decoder='0x1d3aa0',
      boundary='Native serializer with stream output intercepted and native CHBString delegated to separate instance.',
      limitation='Synthetic identities and sizes. Does not establish shared-memory ownership, publication, routing or visibility.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--controller',type=Path,required=True);p.add_argument('--strings',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.controller,a.strings),indent=2))
